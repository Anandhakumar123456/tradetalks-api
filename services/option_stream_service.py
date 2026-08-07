from websocket._exceptions import WebSocketConnectionClosedException

from services.upstox_feed_service import get_streamer


def subscribe_option_keys(option_keys):

    if not option_keys:
        print("❌ No option keys to subscribe")
        return False

    streamer = get_streamer()

    if streamer is None:
        print("❌ Upstox streamer not available")
        return False

    try:

        print(f"📡 Subscribing {len(option_keys)} option instruments")

        streamer.subscribe(
            option_keys,
            "full",
        )

        print("✅ Option subscription request sent")

        return True

    except WebSocketConnectionClosedException:

        print("❌ Upstox WebSocket is closed. Subscription skipped.")

        return False

    except Exception as e:

        print(f"❌ Subscription Error: {e}")

        return False