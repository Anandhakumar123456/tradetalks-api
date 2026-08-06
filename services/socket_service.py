from flask_socketio import SocketIO, emit

socketio = SocketIO(
    cors_allowed_origins="*",
)

# socketio = SocketIO(
#     cors_allowed_origins="*",
#     async_mode="threading",
#     logger=False,
#     engineio_logger=False,
# )