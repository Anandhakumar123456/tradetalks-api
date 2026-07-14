from flask import Blueprint, jsonify

from services.debt_service import get_debt

debt_bp = Blueprint(
    "debt",
    __name__
)


@debt_bp.route("/debt/<symbol>")
def debt(symbol):

    return jsonify(
        get_debt(symbol)
    )