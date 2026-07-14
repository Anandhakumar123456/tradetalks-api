from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from routes.market import market_bp
from routes.option import option_bp
from routes.expiry import expiry_bp
from routes.news import news_bp
from routes.fundamentals import fundamentals_bp
from routes.dividend import dividend_bp
from routes.health import health_bp
from routes.debt import debt_bp
from routes.industry_growth import industry_growth_bp
from routes.valuation import valuation_bp
from routes.risk import risk_bp
from routes.suitability import suitability_bp


# Load environment variables
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Enable CORS
    CORS(app)

    # Register Blueprints
    app.register_blueprint(market_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(option_bp)
    app.register_blueprint(expiry_bp)
    app.register_blueprint(fundamentals_bp)
    app.register_blueprint(dividend_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(debt_bp)
    app.register_blueprint(industry_growth_bp)
    app.register_blueprint(valuation_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(suitability_bp)

    @app.route("/")
    def home():
        return jsonify({
            "status": "online",
            "application": "TradeTalks API",
            "version": "1.0.0"
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error"
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)