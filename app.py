from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import time
from utils.logger import logger

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

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        if request.path == "/favicon.ico":
            return response
        duration = time.time() - getattr(request, "start_time", time.time())
        duration_ms = duration * 1000
        logger.info(
            f"{request.remote_addr} - {request.method} {request.path} "
            f"- {response.status_code} - {duration_ms:.2f}ms"
        )
        return response

    @app.route("/")
    def home():
        return jsonify({
            "status": "online",
            "application": "TradeTalks API",
            "version": "1.0.0"
        })

    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 Not Found: {request.path}")
        return jsonify({
            "error": "Endpoint not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Server Error at {request.path}: {str(error)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error"
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)