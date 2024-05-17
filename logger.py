import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger_name = "sakhi_activity"
log_level = os.environ["LOG_LEVEL"]
log_format = '%(asctime)s - %(thread)d - %(threadName)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
)

# Configure the logger
logger = logging.getLogger(logger_name)
# logger.setLevel(log_level)

# Example usage
# logger.debug("This is a debug message.")
# logger.info("This is an info message.")
# logger.warning("This is a warning message.")
# logger.error("This is an error message.")
# logger.critical("This is a critical message.")