import traceback

from websocket._exceptions import (
    WebSocketConnectionClosedException,
)

from services.upstox_feed_service import (
    get_streamer,
    is_connected,
)


def subscribe_option_keys(option_keys):

    if not option_keys:
        print(
            "❌ No option keys to subscribe"
        )
        return False

    if not is_connected():
        print(
            "❌ Upstox WebSocket is not connected"
        )
        return False

    streamer = get_streamer()

    if streamer is None:
        print(
            "❌ Upstox streamer not available"
        )
        return False

    try:

        print(
            f"📡 Subscribing "
            f"{len(option_keys)} option instruments in batches of 50"
        )

        chunk_size = 50
        for i in range(0, len(option_keys), chunk_size):
            chunk = option_keys[i:i + chunk_size]
            streamer.subscribe(
                chunk,
                "full",
            )

        print(
            f"✅ Option subscription request sent ({len(option_keys)} instruments)"
        )

        return True

    except WebSocketConnectionClosedException:

        print(
            "❌ Upstox WebSocket closed "
            "during subscribe"
        )

        return False

    except Exception as e:

        print(
            f"❌ Subscription Error: {e}"
        )

        traceback.print_exc()

        return False


def unsubscribe_option_keys(option_keys):

    if not option_keys:
        print(
            "❌ No option keys to unsubscribe"
        )
        return False

    if not is_connected():
        print(
            "❌ Upstox WebSocket is not connected"
        )
        return False

    streamer = get_streamer()

    if streamer is None:
        print(
            "❌ Upstox streamer not available"
        )
        return False

    try:

        print(
            f"📤 Unsubscribing "
            f"{len(option_keys)} option instruments in batches of 50"
        )

        chunk_size = 50
        for i in range(0, len(option_keys), chunk_size):
            chunk = option_keys[i:i + chunk_size]
            streamer.unsubscribe(
                chunk,
            )

        print(
            f"✅ Option unsubscription request sent ({len(option_keys)} instruments)"
        )

        return True

    except WebSocketConnectionClosedException:

        print(
            "❌ Upstox WebSocket closed "
            "during unsubscribe"
        )

        return False

    except Exception as e:

        print(
            f"❌ Unsubscription Error: {e}"
        )

        traceback.print_exc()

        return False