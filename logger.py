import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.config.fileConfig('logging.conf')

logger_name = "app"

# Configure the logger
logger = logging.getLogger(logger_name)
logger.setLevel(os.environ["LOG_LEVEL"])

# Example usage
# logger.debug("This is a debug message.")
# logger.info("This is an info message.")
# logger.warning("This is a warning message.")
# logger.error("This is an error message.")
# logger.critical("This is a critical message.")