import logging.config

from scanning.lib.settings import LOGGING


def load_logger():
    """
    This loads logging config
    """
    logging.config.dictConfig(LOGGING)
