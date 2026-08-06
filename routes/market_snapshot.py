from flask import Blueprint, jsonify
from services.market_cache_service import market_cache

market_snapshot_bp = Blueprint(
    "market_snapshot",
    __name__,
)


@market_snapshot_bp.route("/market-snapshot")
def market_snapshot():

    return jsonify(
        market_cache.load()
    )