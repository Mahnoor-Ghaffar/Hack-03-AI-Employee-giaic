import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Maximum file size in bytes (5 MB = 5 * 1024 * 1024 bytes) - Silver Tier requirement
MAX_FILE_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 5  # Keep up to 5 backup log files

def setup_logging(log_file: str = "logs/ai_employee.log", level=logging.INFO, logger_name: str = "ai_employee_logger"):
    """
    Sets up a centralized logging system with file rotation.

    Args:
        log_file: The path to the log file. Default: logs/ai_employee.log
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
        logger_name: Name of the logger instance.

    Returns:
        Configured logger instance.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        # File handler for rotating logs (5MB rotation - Silver Tier requirement)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_FILE_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

        # Console handler for output to stdout
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)

    return logger

# Example usage (for testing, not part of the main application flow)
if __name__ == '__main__':
    logger = setup_logging(level=logging.DEBUG)
    logger.info("Log manager initialized.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    # Simulate writing enough to trigger rotation (if needed)
    # for i in range(1000):
    #     logger.info(f"Test log entry {i}. This is a relatively long line to fill up the file faster. " * 10)
