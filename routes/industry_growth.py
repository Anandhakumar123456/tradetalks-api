from flask import Blueprint, jsonify

from services.industry_growth_service import get_industry_growth

industry_growth_bp = Blueprint(
    "industry_growth",
    __name__
)


@industry_growth_bp.route("/industry-growth/<symbol>")
def industry_growth(symbol):

    return jsonify(
        get_industry_growth(symbol)
    )