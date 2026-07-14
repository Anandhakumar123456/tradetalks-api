from flask import Blueprint, jsonify

from services.valuation_service import get_valuation

valuation_bp = Blueprint(
    "valuation",
    __name__
)


@valuation_bp.route("/valuation/<symbol>")
def valuation(symbol):

    return jsonify(
        get_valuation(symbol)
    )