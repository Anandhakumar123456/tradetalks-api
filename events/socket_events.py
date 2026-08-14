# socket event - updated
# ============================================================

from threading import RLock

from flask import request

from services.socket_service import socketio
from services.option_service import get_option_chain
from services.option_stream_service import (
    subscribe_option_keys,
    unsubscribe_option_keys,
)


# ============================================================
# Connected client option-chain subscription
#
# {
#     socket_sid: {
#         "instrument_key": "...",
#         "expiry": "..."
#     }
# }
#
# This represents only the option chain currently visible
# in the user's UI.
# ============================================================

option_chain_subscribers = {}


# ============================================================
# All option contracts currently subscribed to Upstox stream
# ============================================================

subscribed_option_keys = set()


# ============================================================
# Current UI option-chain contracts required by each client
#
# {
#     socket_sid: {
#         "NSE_FO|123",
#         "NSE_FO|456",
#         ...
#     }
# }
# ============================================================

client_option_chain_keys = {}


# ============================================================
# Open-position contracts required by each client
#
# {
#     socket_sid: {
#         "NSE_FO|123",
#         "NSE_FO|456",
#         ...
#     }
# }
#
# IMPORTANT:
# These contracts must stay live even when the user changes
# the visible option chain.
# ============================================================

client_position_keys = {}


# ============================================================
# Lock
#
# Socket.IO can handle multiple clients concurrently.
# Protect shared subscription state.
# ============================================================

subscription_lock = RLock()


# ============================================================
# CONNECT
# ============================================================

@socketio.on("connect")
def handle_connect():

    sid = request.sid

    with subscription_lock:

        option_chain_subscribers.setdefault(
            sid,
            None,
        )

        client_option_chain_keys.setdefault(
            sid,
            set(),
        )

        client_position_keys.setdefault(
            sid,
            set(),
        )

    print(
        f"✅ Client Connected: {sid}"
    )


# ============================================================
# DISCONNECT
# ============================================================

@socketio.on("disconnect")
def handle_disconnect():

    sid = request.sid

    print(
        f"❌ Client Disconnected: {sid}"
    )

    # --------------------------------------------------------
    # Get every contract required by this client
    #
    # Required = visible option chain + open positions
    # --------------------------------------------------------

    with subscription_lock:

        chain_keys = client_option_chain_keys.pop(
            sid,
            set(),
        )

        position_keys = client_position_keys.pop(
            sid,
            set(),
        )

        option_chain_subscribers.pop(
            sid,
            None,
        )

        client_keys = (
            set(chain_keys)
            | set(position_keys)
        )

        if not client_keys:

            print(
                f"ℹ️ Client {sid} had no option subscriptions"
            )

            return

        # ----------------------------------------------------
        # Find contracts still required by OTHER clients
        # ----------------------------------------------------

        still_required_keys = set()

        for other_chain_keys in (
            client_option_chain_keys.values()
        ):

            still_required_keys.update(
                other_chain_keys
            )

        for other_position_keys in (
            client_position_keys.values()
        ):

            still_required_keys.update(
                other_position_keys
            )

        # ----------------------------------------------------
        # Only contracts that nobody else needs
        # ----------------------------------------------------

        keys_to_unsubscribe = (
            client_keys
            & subscribed_option_keys
        ) - still_required_keys

    # --------------------------------------------------------
    # Nothing to unsubscribe
    # --------------------------------------------------------

    if not keys_to_unsubscribe:

        print(
            "ℹ️ No unused option contracts to unsubscribe"
        )

        return

    print(
        f"📤 Unsubscribing "
        f"{len(keys_to_unsubscribe)} unused option contracts"
    )

    # --------------------------------------------------------
    # Unsubscribe from Upstox
    # --------------------------------------------------------

    success = unsubscribe_option_keys(
        list(keys_to_unsubscribe)
    )

    if success:

        with subscription_lock:

            subscribed_option_keys.difference_update(
                keys_to_unsubscribe
            )

            remaining_count = len(
                subscribed_option_keys
            )

        print(
            f"✅ Unsubscribed "
            f"{len(keys_to_unsubscribe)} contracts"
        )

        print(
            f"📊 Remaining Active Option Contracts: "
            f"{remaining_count}"
        )

    else:

        print(
            "❌ Failed to unsubscribe option contracts"
        )


# ============================================================
# SUBSCRIBE OPTION CHAIN
#
# This handles only the option chain currently shown in UI.
# ============================================================

@socketio.on("subscribe_option_chain")
def subscribe_option_chain(data):

    sid = request.sid

    # --------------------------------------------------------
    # Validate incoming data
    # --------------------------------------------------------

    if not isinstance(data, dict):

        print(
            f"❌ Invalid subscription data "
            f"from {sid}"
        )

        return

    instrument_key = data.get(
        "instrument_key"
    )

    expiry = data.get(
        "expiry"
    )

    if not instrument_key or not expiry:

        print(
            f"❌ Invalid subscription request "
            f"from {sid}"
        )

        return

    instrument_key = str(
        instrument_key
    ).strip()

    expiry = str(
        expiry
    ).strip()

    if not instrument_key or not expiry:

        print(
            f"❌ Empty option-chain subscription request "
            f"from {sid}"
        )

        return

    print(
        f"📥 {sid} requested option chain: "
        f"{instrument_key} ({expiry})"
    )

    # ========================================================
    # DUPLICATE SUBSCRIPTION CHECK
    # ========================================================

    with subscription_lock:

        existing = option_chain_subscribers.get(
            sid
        )

        if (
            existing
            and existing.get("instrument_key")
            == instrument_key
            and existing.get("expiry")
            == expiry
        ):

            print(
                f"ℹ️ Duplicate subscription ignored "
                f"({sid})"
            )

            return

    # ========================================================
    # FETCH OPTION CHAIN
    # ========================================================

    try:

        option_data = get_option_chain(
            instrument_key,
            expiry,
        )

    except Exception as e:

        print(
            f"❌ Failed to fetch option chain "
            f"for {sid}: {e}"
        )

        return

    if not option_data:

        print(
            f"❌ Option chain response is empty "
            f"for {sid}"
        )

        return

    # ========================================================
    # GET STRIKES
    # ========================================================

    strikes = option_data.get(
        "data",
        [],
    )

    if not isinstance(strikes, list):

        print(
            f"❌ Invalid option chain data "
            f"for {sid}"
        )

        return

    print(
        f"📊 Option Chain Strikes: "
        f"{len(strikes)}"
    )

    if not strikes:

        print(
            f"❌ No option contracts found "
            f"for {instrument_key} ({expiry})"
        )

        return

    # ========================================================
    # EXTRACT CE + PE INSTRUMENT KEYS
    # ========================================================

    option_keys = []

    for strike in strikes:

        if not isinstance(strike, dict):
            continue

        # ----------------------------------------------------
        # Call Option / CE
        # ----------------------------------------------------

        call = strike.get(
            "call_options"
        )

        if isinstance(call, dict):

            call_key = call.get(
                "instrument_key"
            )

            if call_key:

                option_keys.append(
                    str(call_key).strip()
                )

        # ----------------------------------------------------
        # Put Option / PE
        # ----------------------------------------------------

        put = strike.get(
            "put_options"
        )

        if isinstance(put, dict):

            put_key = put.get(
                "instrument_key"
            )

            if put_key:

                option_keys.append(
                    str(put_key).strip()
                )

    # ========================================================
    # REMOVE DUPLICATES
    #
    # dict.fromkeys() keeps original order.
    # ========================================================

    option_keys = list(
        dict.fromkeys(
            key
            for key in option_keys
            if key
        )
    )

    print(
        f"📦 Total Option Contracts: "
        f"{len(option_keys)}"
    )

    if not option_keys:

        print(
            "❌ No option instrument keys extracted"
        )

        return

    # ========================================================
    # CHECK PREVIOUS UI OPTION-CHAIN SUBSCRIPTION
    # ========================================================

    with subscription_lock:

        old_client_chain_keys = (
            client_option_chain_keys.get(
                sid,
                set(),
            )
        )

        old_client_chain_keys = set(
            old_client_chain_keys
        )

        globally_subscribed = set(
            subscribed_option_keys
        )

        current_position_keys = set(
            client_position_keys.get(
                sid,
                set(),
            )
        )

    # ========================================================
    # FIND NEW CONTRACTS REQUIRED BY THIS CLIENT
    #
    # Required = new visible chain + existing positions
    # ========================================================

    new_required_keys = (
        set(option_keys)
        | current_position_keys
    )

    new_upstream_keys = [
        key
        for key in new_required_keys
        if key not in globally_subscribed
    ]

    # ========================================================
    # SUBSCRIBE NEW CONTRACTS
    # ========================================================

    if new_upstream_keys:

        print(
            f"📡 Subscribing "
            f"{len(new_upstream_keys)} new contracts"
        )

        success = subscribe_option_keys(
            new_upstream_keys
        )

        if not success:

            print(
                "❌ Option subscription failed"
            )

            return

        # ----------------------------------------------------
        # Only update global state after success
        # ----------------------------------------------------

        with subscription_lock:

            subscribed_option_keys.update(
                new_upstream_keys
            )

        print(
            f"✅ Successfully subscribed "
            f"{len(new_upstream_keys)} new contracts"
        )

    else:

        print(
            "ℹ️ All required contracts are "
            "already subscribed upstream"
        )

    # ========================================================
    # SAVE NEW UI OPTION-CHAIN SUBSCRIPTION
    # ========================================================

    new_client_chain_keys = set(
        option_keys
    )

    with subscription_lock:

        option_chain_subscribers[sid] = {
            "instrument_key": instrument_key,
            "expiry": expiry,
        }

        client_option_chain_keys[sid] = (
            new_client_chain_keys
        )

        total_active_contracts = len(
            subscribed_option_keys
        )

    print(
        f"✅ Client {sid} subscribed to "
        f"{len(new_client_chain_keys)} UI contracts"
    )

    print(
        f"📌 Client {sid} still has "
        f"{len(current_position_keys)} position contracts"
    )

    print(
        f"📊 Total Active Option Contracts: "
        f"{total_active_contracts}"
    )

    # ========================================================
    # CLEANUP OLD UI OPTION-CHAIN CONTRACTS
    #
    # IMPORTANT:
    # Position contracts are protected here.
    #
    # If the user changes:
    #
    # NIFTY expiry A
    #       ↓
    # BANKNIFTY expiry B
    #
    # old chain contracts can be unsubscribed ONLY if:
    # 1. current user no longer needs them
    # 2. current user doesn't hold them as positions
    # 3. another client doesn't need them
    # ========================================================

    if old_client_chain_keys:

        removed_from_chain = (
            old_client_chain_keys
            - new_client_chain_keys
        )

        if removed_from_chain:

            with subscription_lock:

                still_required_by_others = set()

                # Other clients' UI chain contracts
                for (
                    other_sid,
                    other_chain_keys
                ) in client_option_chain_keys.items():

                    if other_sid == sid:
                        continue

                    still_required_by_others.update(
                        other_chain_keys
                    )

                # Other clients' position contracts
                for (
                    other_sid,
                    other_position_keys
                ) in client_position_keys.items():

                    if other_sid == sid:
                        continue

                    still_required_by_others.update(
                        other_position_keys
                    )

                # Current client's own position contracts
                still_required_by_current_client = (
                    current_position_keys
                )

                keys_to_unsubscribe = (
                    removed_from_chain
                    & subscribed_option_keys
                ) - still_required_by_others \
                  - still_required_by_current_client

            if keys_to_unsubscribe:

                print(
                    f"📤 Client {sid} no longer needs "
                    f"{len(keys_to_unsubscribe)} UI-chain contracts"
                )

                success = unsubscribe_option_keys(
                    list(keys_to_unsubscribe)
                )

                if success:

                    with subscription_lock:

                        subscribed_option_keys.difference_update(
                            keys_to_unsubscribe
                        )

                    print(
                        f"✅ Removed "
                        f"{len(keys_to_unsubscribe)} "
                        f"unused UI-chain contracts"
                    )

                else:

                    print(
                        "❌ Failed to unsubscribe "
                        "old UI-chain contracts"
                    )


# ============================================================
# SUBSCRIBE POSITION CONTRACTS
#
# Positions are DIFFERENT from the currently visible option
# chain.
#
# These contracts must remain live even if the user:
#
# NIFTY → BANKNIFTY
# Option Chain → Positions
# Leaves the screen
# Reconnects
#
# The Flutter client sends the exact instrument keys for all
# open positions.
# ============================================================

@socketio.on("subscribe_position_contracts")
def subscribe_position_contracts(data):

    sid = request.sid

    # --------------------------------------------------------
    # Validate incoming data
    # --------------------------------------------------------

    if not isinstance(data, dict):

        print(
            f"❌ Invalid position subscription data "
            f"from {sid}"
        )

        return

    instrument_keys = data.get(
        "instrument_keys"
    )

    if not isinstance(instrument_keys, list):

        print(
            f"❌ Invalid position instrument keys "
            f"from {sid}"
        )

        return

    # --------------------------------------------------------
    # Normalize + remove empty + remove duplicates
    # --------------------------------------------------------

    position_keys = {
        str(key).strip()
        for key in instrument_keys
        if isinstance(key, str)
        and key.strip()
    }

    if not position_keys:

        print(
            f"ℹ️ No position contracts to subscribe "
            f"for {sid}"
        )

        return

    print(
        f"📥 {sid} requested "
        f"{len(position_keys)} position contracts"
    )

    # --------------------------------------------------------
    # Save position requirements SEPARATELY.
    #
    # IMPORTANT:
    # Do NOT use client_option_chain_keys here.
    # ========================================================

    with subscription_lock:

        client_position_keys[sid] = set(
            position_keys
        )

        current_chain_keys = set(
            client_option_chain_keys.get(
                sid,
                set(),
            )
        )

        all_required_by_this_client = (
            current_chain_keys
            | position_keys
        )

        globally_subscribed = set(
            subscribed_option_keys
        )

        new_upstream_keys = [
            key
            for key in all_required_by_this_client
            if key not in globally_subscribed
        ]

    # --------------------------------------------------------
    # Subscribe missing contracts upstream
    # --------------------------------------------------------

    if new_upstream_keys:

        print(
            f"📡 Subscribing "
            f"{len(new_upstream_keys)} "
            f"new position contracts"
        )

        success = subscribe_option_keys(
            new_upstream_keys
        )

        if not success:

            print(
                f"❌ Position contract subscription failed "
                f"for {sid}"
            )

            return

        with subscription_lock:

            subscribed_option_keys.update(
                new_upstream_keys
            )

        print(
            f"✅ Successfully subscribed "
            f"{len(new_upstream_keys)} "
            f"position contracts"
        )

    else:

        print(
            "ℹ️ All position contracts are "
            "already subscribed upstream"
        )

    with subscription_lock:

        total_client_chain = len(
            client_option_chain_keys.get(
                sid,
                set(),
            )
        )

        total_client_positions = len(
            client_position_keys.get(
                sid,
                set(),
            )
        )

        total_active_contracts = len(
            subscribed_option_keys
        )

    print(
        f"✅ Client {sid} position subscriptions: "
        f"{total_client_positions}"
    )

    print(
        f"📊 Client {sid} total required contracts: "
        f"{total_client_chain + total_client_positions}"
    )

    print(
        f"📊 Total Active Option Contracts: "
        f"{total_active_contracts}"
    )


# ============================================================
# OPTIONAL: UNSUBSCRIBE POSITION CONTRACTS
#
# Call this when specific positions are closed.
#
# Example:
# User has:
#   NIFTY 24500 CE
#   NIFTY 24600 CE
#
# User closes:
#   NIFTY 24500 CE
#
# Flutter can send only that exact instrument key here.
# ============================================================

@socketio.on("unsubscribe_position_contracts")
def unsubscribe_position_contracts(data):

    sid = request.sid

    if not isinstance(data, dict):

        print(
            f"❌ Invalid position unsubscribe data "
            f"from {sid}"
        )

        return

    instrument_keys = data.get(
        "instrument_keys"
    )

    if not isinstance(instrument_keys, list):

        print(
            f"❌ Invalid position unsubscribe keys "
            f"from {sid}"
        )

        return

    remove_keys = {
        str(key).strip()
        for key in instrument_keys
        if isinstance(key, str)
        and key.strip()
    }

    if not remove_keys:
        return

    with subscription_lock:

        current_position_keys = set(
            client_position_keys.get(
                sid,
                set(),
            )
        )

        current_position_keys.difference_update(
            remove_keys
        )

        client_position_keys[sid] = (
            current_position_keys
        )

        current_chain_keys = set(
            client_option_chain_keys.get(
                sid,
                set(),
            )
        )

        still_required_by_this_client = (
            current_chain_keys
            | current_position_keys
        )

        still_required_by_others = set()

        # Other clients' UI chain subscriptions
        for other_chain_keys in (
            client_option_chain_keys.values()
        ):

            still_required_by_others.update(
                other_chain_keys
            )

        # Other clients' position subscriptions
        for other_position_keys in (
            client_position_keys.values()
        ):

            still_required_by_others.update(
                other_position_keys
            )

        keys_to_unsubscribe = (
            remove_keys
            & subscribed_option_keys
        ) - still_required_by_this_client \
          - still_required_by_others

    if not keys_to_unsubscribe:

        print(
            f"ℹ️ No position contracts to unsubscribe "
            f"for {sid}"
        )

        return

    print(
        f"📤 Unsubscribing "
        f"{len(keys_to_unsubscribe)} "
        f"closed-position contracts"
    )

    success = unsubscribe_option_keys(
        list(keys_to_unsubscribe)
    )

    if success:

        with subscription_lock:

            subscribed_option_keys.difference_update(
                keys_to_unsubscribe
            )

            remaining_count = len(
                subscribed_option_keys
            )

        print(
            f"✅ Removed "
            f"{len(keys_to_unsubscribe)} "
            f"closed-position contracts"
        )

        print(
            f"📊 Remaining Active Option Contracts: "
            f"{remaining_count}"
        )

    else:

        print(
            "❌ Failed to unsubscribe "
            "closed-position contracts"
        )