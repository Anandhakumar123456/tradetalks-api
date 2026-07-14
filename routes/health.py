from flask import Blueprint, jsonify
from services.health_service import get_health

health_bp = Blueprint(
    "health",
    __name__
)

@health_bp.route("/health/<symbol>")
def health(symbol):
    return jsonify(
        get_health(symbol)
    )