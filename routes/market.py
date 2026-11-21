from flask import Blueprint, jsonify
from services.market_service import get_market_data
from services.market_status_service import get_market_status, is_market_open
from services.websocket_broadcaster import broadcast

market_bp = Blueprint("market", __name__)


@market_bp.route("/market-data", methods=["GET"])
def market_data():
    return jsonify(get_market_data())


@market_bp.route("/market-status", methods=["GET"])
def market_status():
    try:
        status = get_market_status()

        if status is None:
            return jsonify({
                "success": False,
                "status": None,
                "is_market_open": False,
                "message": "Unable to fetch market status",
            }), 503

        # Single source of truth using is_market_open(status)
        is_open = is_market_open(status)

        return jsonify({
            "success": True,
            "status": status,
            "is_market_open": is_open,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "status": None,
            "is_market_open": False,
            "message": str(e),
        }), 500
