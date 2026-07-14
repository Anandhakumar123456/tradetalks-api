import os
import logging
from logging.handlers import RotatingFileHandler
import colorama
from config import DEBUG

# Initialize colorama for Windows console support
colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: colorama.Fore.CYAN,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.WHITE + colorama.Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        reset = colorama.Style.RESET_ALL if color else ""

        orig_levelname = record.levelname
        record.levelname = f"{color}{orig_levelname}{reset}"

        result = super().format(record)
        record.levelname = orig_levelname
        return result


def setup_logger(name="TradeTalks"):
    # Determine base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_filepath = os.path.join(logs_dir, "app.log")

    logger = logging.getLogger(name)

    # Set the logging level based on debug configuration
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            log_filepath,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        console_formatter = ColoredFormatter(
            "[%(asctime)s] %(levelname)-8s in %(filename)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()