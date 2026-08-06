import upstox_client

from services.upstox_service import api_client
from services.socket_service import socketio
from services.market_cache_service import market_cache

streamer = upstox_client.MarketDataStreamerV3(api_client)

# Live market data (temporary)
live_market = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None,
}

instrument_mapping = {
    "NSE_INDEX|Nifty 50": "NIFTY",
    "NSE_INDEX|Nifty Bank": "BANKNIFTY",
    "BSE_INDEX|SENSEX": "SENSEX",
}

option_cache = {}


def on_open():
    print("🟢 Upstox WebSocket Connected")

    streamer.subscribe(
        [
            "NSE_INDEX|Nifty 50",
            "NSE_INDEX|Nifty Bank",
            "BSE_INDEX|SENSEX",
        ],
        "ltpc",
    )

    print("📡 Subscribed to NIFTY, BANKNIFTY & SENSEX")


def on_close():
    print("🔴 Upstox WebSocket Closed")


def on_error(error):
    print("❌ Error:", error)


def on_message(message):
    print("🔥 MESSAGE RECEIVED")

    if "feeds" not in message:
        return

    feeds = message["feeds"]

    for instrument_key, feed in feeds.items():

        # -----------------------------
        # MARKET INDEX TICKS
        # -----------------------------
        if instrument_key in instrument_mapping:

            ltpc = feed.get("ltpc")

            if not ltpc:
                continue

            title = instrument_mapping[instrument_key]

            last_price = float(ltpc.get("ltp", 0))
            previous_close = float(ltpc.get("cp", 0))

            net_change = last_price - previous_close

            percent_change = (
                (net_change / previous_close) * 100
                if previous_close != 0
                else 0
            )

            live_market[title] = {
                "title": title,
                "price": f"{last_price:,.2f}",
                "change": f"{net_change:+.2f} ({percent_change:.2f}%)",
                "percent_change": round(percent_change, 2),
                "open": 0,
                "high": 0,
                "low": 0,
                "previous_close": previous_close,
                "isBullish": net_change >= 0,
            }

        # -----------------------------
        # OPTION TICKS
        # -----------------------------
        else:

            full_feed = feed.get("fullFeed")

            if not full_feed:
                continue

            market_ff = full_feed.get("marketFF")

            if not market_ff:
                continue

            ltpc = market_ff.get("ltpc")

            if not ltpc:
                continue

            greeks = market_ff.get("optionGreeks", {})

            option_cache[instrument_key] = {
                "instrument_key": instrument_key,
                "ltp": ltpc.get("ltp"),
                "cp": ltpc.get("cp"),
                "oi": market_ff.get("oi"),
                "iv": market_ff.get("iv"),
                "delta": greeks.get("delta"),
                "theta": greeks.get("theta"),
                "gamma": greeks.get("gamma"),
                "vega": greeks.get("vega"),
            }

    # -----------------------------
    # MARKET UPDATE
    # -----------------------------
    market_payload = [
        data
        for data in [
            live_market["NIFTY"],
            live_market["BANKNIFTY"],
            live_market["SENSEX"],
        ]
        if data is not None
    ]

    if market_payload:

        # Save latest snapshot (RAM + JSON)
        print(f"💾 Saving snapshot: {len(market_payload)} items")
        market_cache.save(market_payload)

        # Send to Flutter
        socketio.emit(
            "market_update",
            market_payload,
            namespace="/",
        )

    # -----------------------------
    # OPTION UPDATE
    # -----------------------------
    option_payload = list(option_cache.values())

    if option_payload:

        socketio.emit(
            "option_chain_update",
            option_payload,
            namespace="/",
        )


streamer.on("open", on_open)
streamer.on("close", on_close)
streamer.on("error", on_error)
streamer.on("message", on_message)


def start_upstox_feed():
    print("🚀 Starting Upstox Feed...")
    streamer.connect()


def get_streamer():
    return streamer