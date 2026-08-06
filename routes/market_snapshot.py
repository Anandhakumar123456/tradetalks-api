# from flask import Blueprint, jsonify
# from services.market_cache_service import market_cache

# market_snapshot_bp = Blueprint(
#     "market_snapshot",
#     __name__,
# )


# @market_snapshot_bp.route("/market-snapshot")
# def market_snapshot():
#     print("LOAD INSTANCE:", id(market_cache))
#     print("DATA:", market_cache.load())

#     return jsonify(
#         market_cache.load()
#     )

import json
import os
from flask import Blueprint, jsonify

market_snapshot_bp = Blueprint(
    "market_snapshot",
    __name__,
)

@market_snapshot_bp.route("/market-snapshot")
def market_snapshot():

    print("FILE EXISTS:", os.path.exists("market_snapshot.json"))

    if not os.path.exists("market_snapshot.json"):
        return jsonify([])

    with open("market_snapshot.json", "r") as f:
        data = json.load(f)

    print("FILE DATA:", data)

    return jsonify(data)