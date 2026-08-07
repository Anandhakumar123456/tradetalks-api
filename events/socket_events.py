from flask import request

from services.socket_service import socketio
from services.option_service import get_option_chain
from services.option_stream_service import subscribe_option_keys

# Connected clients
option_chain_subscribers = {}

# Already subscribed option contracts
subscribed_option_keys = set()


@socketio.on("connect")
def handle_connect():
    print(f"✅ Client Connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    option_chain_subscribers.pop(request.sid, None)
    print(f"❌ Client Disconnected: {request.sid}")


@socketio.on("subscribe_option_chain")
def subscribe_option_chain(data):

    instrument_key = data.get("instrument_key")
    expiry = data.get("expiry")

    if not instrument_key or not expiry:
        print("❌ Invalid subscription request")
        return

    option_chain_subscribers[request.sid] = {
        "instrument_key": instrument_key,
        "expiry": expiry,
    }

    print(
        f"📥 {request.sid} subscribed to "
        f"{instrument_key} ({expiry})"
    )

    # -----------------------------
    # Fetch Option Chain
    # -----------------------------
    try:
        option_data = get_option_chain(
            instrument_key,
            expiry,
        )
    except Exception as e:
        print(f"❌ Failed to fetch option chain: {e}")
        return

    # -----------------------------
    # Collect CE & PE instrument keys
    # -----------------------------
    option_keys = []

    for strike in option_data.get("data", []):

        call = strike.get("call_options")
        put = strike.get("put_options")

        if call and call.get("instrument_key"):
            option_keys.append(call["instrument_key"])

        if put and put.get("instrument_key"):
            option_keys.append(put["instrument_key"])

    # Remove duplicates
    option_keys = list(set(option_keys))

    if not option_keys:
        print("❌ No option instrument keys found")
        return

    # -----------------------------
    # Subscribe only NEW contracts
    # -----------------------------
    new_keys = [
        key
        for key in option_keys
        if key not in subscribed_option_keys
    ]

    if not new_keys:
        print("ℹ️ All option contracts already subscribed")
        return

    print(f"📡 Subscribing {len(new_keys)} new contracts")

    success = subscribe_option_keys(new_keys)

    if success:
        subscribed_option_keys.update(new_keys)

        print(
            f"✅ Total Active Option Contracts: "
            f"{len(subscribed_option_keys)}"
        )
    else:
        print("❌ Subscription failed. Will retry on next request.")