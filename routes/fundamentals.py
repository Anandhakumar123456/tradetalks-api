from flask import Blueprint, jsonify

from services.fundamentals_service import get_fundamentals

fundamentals_bp = Blueprint(
    "fundamentals",
    __name__
)

@fundamentals_bp.route("/fundamentals/<symbol>")
def fundamentals(symbol):

    return jsonify(
        get_fundamentals(symbol)
    )