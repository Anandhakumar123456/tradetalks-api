import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import events.socket_events

from utils.logger import logger

from services.socket_service import socketio
from services.upstox_feed_service import start_upstox_feed

from scheduler.startup import start_all_schedulers

from routes.market import market_bp
from routes.news import news_bp
from routes.market_snapshot import market_snapshot_bp
from routes.option import option_bp
from routes.expiry import expiry_bp
from routes.fundamentals import fundamentals_bp
from routes.dividend import dividend_bp
from routes.health import health_bp
from routes.debt import debt_bp
from routes.industry_growth import industry_growth_bp
from routes.valuation import valuation_bp
from routes.risk import risk_bp
from routes.suitability import suitability_bp
from routes.notification import notification_bp


load_dotenv()

_feed_started = False


def create_app():

    app = Flask(__name__)

    CORS(app)

    # -----------------------------
    # Blueprints
    # -----------------------------

    app.register_blueprint(market_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(market_snapshot_bp)
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
    app.register_blueprint(notification_bp)

    # -----------------------------
    # Scheduler
    # -----------------------------

    start_all_schedulers()

    # -----------------------------
    # Start Upstox Feed only once
    # -----------------------------

    @app.before_request
    def ensure_feed():

        global _feed_started

        if not _feed_started:

            start_upstox_feed()

            _feed_started = True

    # -----------------------------
    # Request Logging
    # -----------------------------

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):

        if request.path == "/favicon.ico":
            return response

        duration = (
            time.time()
            - getattr(request, "start_time", time.time())
        )

        logger.info(
            f"{request.remote_addr} - "
            f"{request.method} "
            f"{request.path} - "
            f"{response.status_code} - "
            f"{duration * 1000:.2f}ms"
        )

        return response

    # -----------------------------
    # Routes
    # -----------------------------

    @app.route("/")
    def home():

        return jsonify(
            {
                "status": "online",
                "application": "TradeTalks API",
                "version": "1.0.0",
            }
        )

    # -----------------------------
    # Error Handlers
    # -----------------------------

    @app.errorhandler(404)
    def not_found(error):

        logger.warning(f"404 Not Found : {request.path}")

        return jsonify(
            {
                "error": "Endpoint not found",
            }
        ), 404

    @app.errorhandler(500)
    def internal_error(error):

        logger.exception(error)

        return jsonify(
            {
                "error": "Internal Server Error",
            }
        ), 500

    return app


app = create_app()

socketio.init_app(app)


if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True,
    )