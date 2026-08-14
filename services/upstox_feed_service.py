import threading
import time

import upstox_client

from services.market_cache_service import market_cache
from services.socket_service import socketio
from services.upstox_service import api_client


# ============================================================
# UPSTOX STREAMER STATE
# ============================================================

streamer = None

streamer_lock = threading.RLock()
connection_lock = threading.Lock()

connected = False
reconnect_running = False

# Used to identify the currently active streamer.
# Old streamer callbacks should not affect the new streamer.
streamer_generation = 0


# ============================================================
# RECONNECT CONFIGURATION
# ============================================================

RECONNECT_INITIAL_DELAY = 5
RECONNECT_MAX_DELAY = 60

# Maximum number of consecutive reconnect attempts before
# waiting longer and starting again.
RECONNECT_MAX_ATTEMPTS = 10


# ============================================================
# LIVE MARKET DATA
# ============================================================

live_market = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None,
}


# ============================================================
# INDEX INSTRUMENT MAPPING
# ============================================================

instrument_mapping = {
    "NSE_INDEX|Nifty 50": "NIFTY",
    "NSE_INDEX|Nifty Bank": "BANKNIFTY",
    "BSE_INDEX|SENSEX": "SENSEX",
}


INDEX_KEYS = [
    "NSE_INDEX|Nifty 50",
    "NSE_INDEX|Nifty Bank",
    "BSE_INDEX|SENSEX",
]


# ============================================================
# OPTION CACHE
# ============================================================

option_cache = {}

option_cache_lock = threading.Lock()


# ============================================================
# OPTION SUBSCRIPTION STATE
# ============================================================
#
# This set represents option contracts that the application
# wants to keep subscribed to at the feed level.
#
# Your option subscription manager can continue using its
# existing logic.
# ============================================================

feed_subscribed_option_keys = set()

feed_subscription_lock = threading.Lock()


# ============================================================
# CREATE STREAMER
# ============================================================

def create_streamer():
    """
    Create a new Upstox MarketDataStreamerV3 instance
    and attach all callbacks.
    """

    global streamer
    global streamer_generation

    new_streamer = upstox_client.MarketDataStreamerV3(
        api_client
    )

    # Every newly created streamer gets a new generation ID.
    streamer_generation += 1
    current_generation = streamer_generation

    # --------------------------------------------------------
    # IMPORTANT:
    # Use *args because Upstox callback signatures can provide
    # additional arguments.
    # --------------------------------------------------------

    def handle_open(*args):
        on_open(current_generation, *args)

    def handle_close(*args):
        on_close(current_generation, *args)

    def handle_error(error=None, *args):
        on_error(current_generation, error, *args)

    def handle_message(message, *args):
        on_message(message)

    new_streamer.on(
        "open",
        handle_open,
    )

    new_streamer.on(
        "close",
        handle_close,
    )

    new_streamer.on(
        "error",
        handle_error,
    )

    new_streamer.on(
        "message",
        handle_message,
    )

    streamer = new_streamer

    print(
        f"🆕 Upstox streamer created "
        f"(generation={current_generation})"
    )

    return new_streamer


# ============================================================
# CHECK ACTIVE STREAMER
# ============================================================

def _is_current_streamer(generation):
    """
    Prevent callbacks from old/dead streamers from modifying
    the state of the currently active streamer.
    """

    with connection_lock:
        return generation == streamer_generation


# ============================================================
# STREAM OPEN
# ============================================================

def on_open(generation, *args):
    """
    Called when Upstox WebSocket connection is established.
    """

    global connected
    global reconnect_running

    # Ignore callbacks from old streamer instances.
    if not _is_current_streamer(generation):
        print(
            "ℹ️ Ignoring open event from old streamer "
            f"(generation={generation})"
        )
        return

    with connection_lock:
        connected = True
        reconnect_running = False

    print(
        "🟢 Upstox WebSocket Connected"
    )

    # --------------------------------------------------------
    # Subscribe index instruments
    # --------------------------------------------------------

    current_streamer = get_streamer()

    if current_streamer is None:
        print(
            "❌ Streamer unavailable on open"
        )
        return

    try:
        current_streamer.subscribe(
            INDEX_KEYS,
            "ltpc",
        )

        print(
            "📡 Subscribed to "
            "NIFTY, BANKNIFTY & SENSEX"
        )

    except Exception as e:
        print(
            f"❌ Failed to subscribe index feed: {e}"
        )

    # --------------------------------------------------------
    # Restore option subscriptions
    # --------------------------------------------------------

    with feed_subscription_lock:
        option_keys = list(
            feed_subscribed_option_keys
        )

    if not option_keys:
        return

    try:
        current_streamer.subscribe(
            option_keys,
            "full",
        )

        print(
            f"📡 Restored {len(option_keys)} "
            "option subscriptions"
        )

    except Exception as e:
        print(
            f"❌ Failed to restore option subscriptions: {e}"
        )


# ============================================================
# STREAM CLOSE
# ============================================================

def on_close(generation, *args):
    """
    Called when Upstox WebSocket closes.

    IMPORTANT:
    The callback accepts *args because the SDK can pass
    additional callback parameters.
    """

    global connected

    # Ignore old streamer callbacks.
    if not _is_current_streamer(generation):
        print(
            "ℹ️ Ignoring close event from old streamer "
            f"(generation={generation})"
        )
        return

    with connection_lock:
        connected = False

    print(
        "🔴 Upstox WebSocket Closed"
    )

    # Only one reconnect worker can run.
    start_reconnect()


# ============================================================
# STREAM ERROR
# ============================================================

def on_error(generation, error=None, *args):
    """
    Called when Upstox reports a WebSocket error.
    """

    global connected

    # Ignore old streamer callbacks.
    if not _is_current_streamer(generation):
        print(
            "ℹ️ Ignoring error event from old streamer "
            f"(generation={generation})"
        )
        return

    with connection_lock:
        connected = False

    print(
        f"❌ Upstox WebSocket Error: {error}"
    )

    # Only one reconnect worker can run.
    start_reconnect()


# ============================================================
# START RECONNECT
# ============================================================

def start_reconnect():
    """
    Start exactly one reconnect worker.

    Multiple Upstox callbacks can call this function, but
    only one worker will actually be created.
    """

    global reconnect_running

    with connection_lock:

        if connected:
            return

        if reconnect_running:
            print(
                "ℹ️ Reconnect worker already running"
            )
            return

        reconnect_running = True

    thread = threading.Thread(
        target=reconnect_worker,
        daemon=True,
        name="upstox-reconnect",
    )

    thread.start()


# ============================================================
# RECONNECT WORKER
# ============================================================

def reconnect_worker():
    """
    Single controlled reconnect loop.

    Uses exponential backoff to prevent reconnect storms
    and Upstox 429 responses.
    """

    global streamer
    global connected
    global reconnect_running

    delay = RECONNECT_INITIAL_DELAY
    attempt = 0

    try:

        while True:

            # ------------------------------------------------
            # Already connected?
            # ------------------------------------------------

            with connection_lock:

                if connected:
                    print(
                        "✅ Reconnect worker stopped - "
                        "connection is active"
                    )
                    return

            attempt += 1

            print(
                f"🔄 Upstox reconnect attempt "
                f"#{attempt}"
            )

            try:

                # ------------------------------------------------
                # Create and connect a new streamer
                # ------------------------------------------------

                with streamer_lock:

                    # Check again before creating.
                    with connection_lock:
                        if connected:
                            return

                    new_streamer = create_streamer()

                    new_streamer.connect()

                # ------------------------------------------------
                # connect() may return before on_open.
                # Wait for actual open callback.
                # ------------------------------------------------

                connected_successfully = False

                for _ in range(10):

                    time.sleep(1)

                    with connection_lock:

                        if connected:
                            connected_successfully = True
                            break

                if connected_successfully:

                    print(
                        "✅ Upstox Feed Reconnected"
                    )

                    return

                print(
                    "⚠️ Reconnect attempt timed out"
                )

            except Exception as e:

                print(
                    f"❌ Reconnect Failed: {e}"
                )

            # ------------------------------------------------
            # Exponential backoff
            #
            # 5
            # 10
            # 20
            # 40
            # 60
            # 60
            # ...
            # ------------------------------------------------

            print(
                f"⏳ Waiting {delay}s before next "
                "Upstox reconnect attempt"
            )

            time.sleep(delay)

            delay = min(
                delay * 2,
                RECONNECT_MAX_DELAY,
            )

            # ------------------------------------------------
            # Avoid an infinite extremely-fast retry loop.
            #
            # We don't permanently disable reconnecting.
            # After MAX attempts, reset the counter and
            # continue with the maximum delay.
            # ------------------------------------------------

            if attempt >= RECONNECT_MAX_ATTEMPTS:

                print(
                    "⚠️ Maximum reconnect attempts reached. "
                    "Continuing with controlled backoff."
                )

                attempt = 0

    finally:

        with connection_lock:
            reconnect_running = False


# ============================================================
# MARKET MESSAGE HANDLER
# ============================================================

def on_message(message):
    """
    Process incoming Upstox market data.
    """

    if not isinstance(message, dict):
        return

    feeds = message.get("feeds")

    if not isinstance(feeds, dict):
        return

    changed_market = []
    changed_options = []

    # ========================================================
    # PROCESS FEEDS
    # ========================================================

    for instrument_key, feed in feeds.items():

        if not isinstance(feed, dict):
            continue

        # ====================================================
        # INDEX FEED
        # ====================================================

        if instrument_key in instrument_mapping:

            ltpc = feed.get("ltpc")

            if not isinstance(ltpc, dict):
                continue

            title = instrument_mapping[
                instrument_key
            ]

            try:

                last_price = float(
                    ltpc.get(
                        "ltp",
                        0,
                    )
                    or 0
                )

                previous_close = float(
                    ltpc.get(
                        "cp",
                        0,
                    )
                    or 0
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            if last_price <= 0:
                continue

            change = (
                last_price
                - previous_close
            )

            percent = (
                (change / previous_close) * 100
                if previous_close
                else 0
            )

            market_item = {
                "title": title,
                "price": f"{last_price:,.2f}",
                "change": (
                    f"{change:+.2f} "
                    f"({percent:.2f}%)"
                ),
                "percent_change": round(
                    percent,
                    2,
                ),
                "open": 0,
                "high": 0,
                "low": 0,
                "previous_close": previous_close,
                "isBullish": change >= 0,
            }

            live_market[title] = market_item

            changed_market.append(
                market_item
            )

        # ====================================================
        # OPTION FEED
        # ====================================================

        else:

            full_feed = feed.get(
                "fullFeed"
            )

            if not isinstance(full_feed, dict):
                continue

            market_ff = full_feed.get(
                "marketFF"
            )

            if not isinstance(market_ff, dict):
                continue

            ltpc = market_ff.get(
                "ltpc"
            )

            if not isinstance(ltpc, dict):
                continue

            greeks = market_ff.get(
                "optionGreeks",
                {},
            )

            if not isinstance(
                greeks,
                dict,
            ):
                greeks = {}

            option_data = {
                "instrument_key": instrument_key,

                "ltp": ltpc.get(
                    "ltp"
                ),

                "cp": ltpc.get(
                    "cp"
                ),

                "oi": market_ff.get(
                    "oi"
                ),

                "iv": market_ff.get(
                    "iv"
                ),

                "delta": greeks.get(
                    "delta"
                ),

                "theta": greeks.get(
                    "theta"
                ),

                "gamma": greeks.get(
                    "gamma"
                ),

                "vega": greeks.get(
                    "vega"
                ),
            }

            # ------------------------------------------------
            # Update option cache only when data changed.
            # ------------------------------------------------

            with option_cache_lock:

                old_data = option_cache.get(
                    instrument_key
                )

                if old_data == option_data:
                    continue

                option_cache[
                    instrument_key
                ] = option_data

            changed_options.append(
                option_data
            )

    # ========================================================
    # MARKET UPDATE
    # ========================================================

    if changed_market:

        market_payload = [
            live_market["NIFTY"],
            live_market["BANKNIFTY"],
            live_market["SENSEX"],
        ]

        market_payload = [
            item
            for item in market_payload
            if item is not None
        ]

        if market_payload:

            # ------------------------------------------------
            # Save latest market snapshot.
            # ------------------------------------------------

            try:

                market_cache.save(
                    market_payload
                )

            except Exception as e:

                print(
                    f"⚠️ Market cache save failed: {e}"
                )

            # ------------------------------------------------
            # Send to Flutter.
            # ------------------------------------------------

            try:

                socketio.emit(
                    "market_update",
                    market_payload,
                    namespace="/",
                )

            except Exception as e:

                print(
                    f"⚠️ Market socket emit failed: {e}"
                )

    # ========================================================
    # OPTION UPDATE
    # ========================================================

    if changed_options:

        for option in changed_options:

            try:

                socketio.emit(
                    "option_update",
                    option,
                    namespace="/",
                )

            except Exception as e:

                print(
                    f"⚠️ Option socket emit failed: {e}"
                )


# ============================================================
# START UPSTOX FEED
# ============================================================

def start_upstox_feed():
    """
    Start the Upstox feed exactly once.

    If initial connection fails, the controlled reconnect
    worker takes over.
    """

    global streamer
    global connected

    with streamer_lock:

        with connection_lock:

            if connected:
                print(
                    "ℹ️ Upstox Feed already connected"
                )
                return

            if streamer is not None:
                print(
                    "ℹ️ Upstox streamer already exists"
                )

        print(
            "🚀 Starting Upstox Feed..."
        )

        try:

            new_streamer = create_streamer()

            new_streamer.connect()

        except Exception as e:

            print(
                f"❌ Failed to start Upstox Feed: {e}"
            )

            with connection_lock:
                connected = False

            start_reconnect()


# ============================================================
# GET STREAMER
# ============================================================

def get_streamer():
    """
    Return current Upstox streamer instance.
    """

    with streamer_lock:
        return streamer


# ============================================================
# CONNECTION STATUS
# ============================================================

def is_connected():
    """
    Return current Upstox WebSocket connection status.
    """

    with connection_lock:
        return connected