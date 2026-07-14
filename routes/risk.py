from flask import Blueprint, jsonify

from services.risk_service import get_risk

risk_bp = Blueprint(
    "risk",
    __name__
)


@risk_bp.route("/risk/<symbol>")
def risk(symbol):

    return jsonify(
        get_risk(symbol)
    )