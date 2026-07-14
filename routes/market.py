from flask import Blueprint, jsonify
from services.market_service import get_market_data

market_bp = Blueprint("market", __name__)

@market_bp.route("/market-data", methods=["GET"])
def market_data():
    return jsonify(get_market_data())