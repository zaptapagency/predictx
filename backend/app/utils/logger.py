import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings


def setup_logger(name: str) -> logging.Logger:
    """Setup JSON logger for application"""

    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


# Create module-level logger
logger = setup_logger(__name__)
