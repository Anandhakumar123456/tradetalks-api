from services.socket_service import socketio

def broadcast(event, data):
    socketio.emit(
        event,
        data,
        namespace="/",
    )