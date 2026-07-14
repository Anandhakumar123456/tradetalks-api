from flask import Blueprint, jsonify

from services.suitability_service import get_suitability

suitability_bp = Blueprint(
    "suitability",
    __name__
)


@suitability_bp.route("/investor-suitability/<symbol>")
def suitability(symbol):

    return jsonify(
        get_suitability(symbol)
    )