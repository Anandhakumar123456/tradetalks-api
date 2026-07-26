"""
Firebase service for sending user and topic notifications.
"""

import firebase_admin
from firebase_admin import credentials, firestore, messaging

from utils.logger import logger


SERVICE_ACCOUNT_KEY = "serviceAccountKey.json"
USERS_COLLECTION = "users"


if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)

db = firestore.client()


def get_fcm_token(uid: str) -> str | None:
    """
    Fetch the FCM token for a user.
    """

    try:

        doc = db.collection(USERS_COLLECTION).document(uid).get()

        if not doc.exists:
            return None

        data = doc.to_dict() or {}

        return data.get("fcm_token")

    except Exception as e:

        logger.error(
            f"Failed to fetch FCM token for user={uid}: {e}"
        )

        return None


def send_topic_notification(
    topic: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> str:
    """
    Send notification to a topic.
    """

    try:

        message = messaging.Message(
            topic=topic,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
        )

        message_id = messaging.send(message)

        logger.info(
            f"Topic notification sent. topic={topic}, message_id={message_id}"
        )

        return message_id

    except Exception as e:

        logger.error(
            f"Failed to send topic notification: {e}"
        )

        raise


def send_notification(
    uid: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> str:
    """
    Send notification to a single user.
    """

    token = get_fcm_token(uid)

    if not token:
        raise ValueError(
            f"FCM token not found for user: {uid}"
        )

    try:

        message = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
        )

        message_id = messaging.send(message)

        logger.info(
            f"Notification sent. user={uid}, message_id={message_id}"
        )

        return message_id

    except Exception as e:

        logger.error(
            f"Failed to send notification to user={uid}: {e}"
        )

        raise