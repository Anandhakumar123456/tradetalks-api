from flask import Blueprint, jsonify

from services.firebase_service import (
    send_notification,
    send_topic_notification,
)

notification_bp = Blueprint("notification", __name__)

# Development/Test Configuration
TEST_UID = "z49G1E3m8jamu4qS2QL9ZpE5tkz1"

TEST_TITLE = "TradeTalks 🚀"
TEST_BODY = "Hello Boss! Push Notification Working Successfully 🎉"
TOPIC_NAME = "tradetalks_all"


@notification_bp.route("/test-notification", methods=["GET"])
def test_notification():
    """Send a test notification to a specific user."""

    try:
        message_id = send_notification(
            uid=TEST_UID,
            title=TEST_TITLE,
            body=TEST_BODY,
        )

        return jsonify({
            "success": True,
            "message": "Test notification sent successfully.",
            "message_id": message_id,
            "uid": TEST_UID,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to send test notification.",
            "error": str(e),
        }), 500


@notification_bp.route("/test-topic", methods=["GET"])
def test_topic():
    """Send a test topic notification."""

    try:
        message_id = send_topic_notification(
            topic=TOPIC_NAME,
            title=TEST_TITLE,
            body="Testing Topic Notification",
        )

        return jsonify({
            "success": True,
            "message": "Topic notification sent successfully.",
            "message_id": message_id,
            "topic": TOPIC_NAME,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to send topic notification.",
            "error": str(e),
        }), 500