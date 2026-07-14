from flask import Blueprint, jsonify
from services.dividend_service import get_dividend

dividend_bp = Blueprint(
    "dividend",
    __name__
)

@dividend_bp.route("/dividend/<symbol>")
def dividend(symbol):

    return jsonify(
        get_dividend(symbol)
    )