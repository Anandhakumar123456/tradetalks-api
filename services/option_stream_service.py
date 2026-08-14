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
            f"{len(option_keys)} option instruments"
        )

        streamer.subscribe(
            option_keys,
            "full",
        )

        print(
            "✅ Option subscription request sent"
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
            f"{len(option_keys)} option instruments"
        )

        streamer.unsubscribe(
            option_keys,
        )

        print(
            "✅ Option unsubscription request sent"
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