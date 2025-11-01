import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def create_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False

    std_handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    std_handler.setFormatter(formatter)
    logger.addHandler(std_handler)

    logger.setLevel(logging.DEBUG)

    return logger
