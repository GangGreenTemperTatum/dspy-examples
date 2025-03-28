import sys

from loguru import logger

# create a nice logger using emojis and colorful text that can be used throughout the codebase
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)
logger.add(
    "logs.log",
    rotation="1 week",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)
logger.level("DEBUG")
