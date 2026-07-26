from firebase_admin import firestore

from scheduler.scheduler import scheduler
from services.firebase_service import send_notification
from utils.logger import logger

db = firestore.client()

LEVELS = {
    "beginner": ["b1", "b2", "b3", "b4", "b5"],
    "intermediate": ["i1", "i2", "i3", "i4", "i5"],
    "advanced": ["a1", "a2", "a3", "a4", "a5", "a6"],
    "expert": ["e1", "e2", "e3", "e4", "e5", "e6"],
}


def get_all_users():
    """Return all user documents."""
    return db.collection("users").stream()


def get_level_status(
    progress: dict,
    lesson_ids: list[str],
) -> tuple[bool, bool]:
    """
    Determine whether a level has been started and completed.
    """

    started = False
    completed = True

    for lesson_id in lesson_ids:

        lesson = progress.get(lesson_id, {})

        if lesson.get("isStarted") or lesson.get("isCompleted"):
            started = True

        if not lesson.get("isCompleted", False):
            completed = False

    return started, completed


def check_learning_reminders():
    """
    Send learning reminders to users
    who have started but not completed a level.
    """

    logger.info("Learning reminder scheduler started.")

    users = get_all_users()

    for user in users:

        try:

            data = user.to_dict() or {}

            progress = data.get("lesson_progress", {})

            if not progress:
                continue

            for level, lessons in LEVELS.items():

                started, completed = get_level_status(
                    progress,
                    lessons,
                )

                if started and not completed:

                    send_notification(
                        user.id,
                        "📚 Continue Learning",
                        f"Continue your {level.title()} course today!",
                        data={
                            "screen": "learn",
                            "course": level,  #level.lower() if not useed this 
                        },
                    )

                    logger.info(
                        f"Learning reminder sent to user={user.id}, level={level}"
                    )

                    break

        except Exception as e:

            logger.error(
                f"Failed to send learning reminder to user={user.id}: {e}"
            )

    logger.info("Learning reminder scheduler completed.")


def start_learning_scheduler():
    """Register learning reminder scheduler."""

    scheduler.add_job(
        check_learning_reminders,
        trigger="cron",
        hour=19,           # default time is 19
        minute=0,
        id="learning_reminder",
        replace_existing=True,
    )