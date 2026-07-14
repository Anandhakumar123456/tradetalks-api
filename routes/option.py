from flask import Blueprint, request, jsonify

from services.option_service import get_option_chain

option_bp = Blueprint(
    "option",
    __name__
)


@option_bp.route("/option-chain", methods=["GET"])
def option_chain():

    instrument_key = request.args.get("instrument_key")
    expiry = request.args.get("expiry")

    if not instrument_key:
        return jsonify({
            "error": "instrument_key is required"
        }), 400

    if not expiry:
        return jsonify({
            "error": "expiry is required"
        }), 400

    data = get_option_chain(
        instrument_key,
        expiry
    )

    return jsonify(data)