from scheduler.scheduler import scheduler
from services.market_service import get_market_data
from services.websocket_broadcaster import broadcast
from utils.logger import logger


from services.socket_service import socketio

def broadcast_live_market():
    logger.info("🚀 Live market scheduler triggered")

    try:
        data = get_market_data()

        socketio.emit(
            "market_update",
            data,
            namespace="/",
        )

        logger.info("📡 SocketIO emit completed")

    except Exception as e:
        logger.exception(f"Live market broadcast failed: {e}")
        
def start_live_market_scheduler():
    scheduler.add_job(
        broadcast_live_market,
        trigger="interval",
        seconds=1,
        id="live_market_scheduler",
        replace_existing=True,
    )

    logger.info("✅ Live Market Scheduler registered.")