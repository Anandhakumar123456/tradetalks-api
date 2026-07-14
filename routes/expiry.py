from flask import Blueprint, request, jsonify

from services.expiry_service import get_expiry_list

expiry_bp = Blueprint(
    "expiry",
    __name__
)


@expiry_bp.route("/expiry-list", methods=["GET"])
def expiry_list():

    instrument_key = request.args.get("instrument_key")

    if not instrument_key:
        return jsonify({
            "error": "instrument_key is required"
        }), 400

    data = get_expiry_list(instrument_key)

    return jsonify(data)