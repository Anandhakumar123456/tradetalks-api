from services.upstox_feed_service import get_streamer


def subscribe_option_keys(option_keys):

    if not option_keys:
        print("❌ No option keys to subscribe")
        return

    streamer = get_streamer()

    print(f"📡 Subscribing {len(option_keys)} option instruments")

    streamer.subscribe(
        option_keys,
        "full",
    )

    print("✅ Option subscription request sent")