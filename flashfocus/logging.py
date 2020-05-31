"""Module for adding color to logging output."""
import logging
import sys


ANSI = {"green": "\033[92m", "red": "\033[91m", "end": "\033[0m"}


def red(x):
    """Color text red using ANSI escape sequences."""
    return ANSI["red"] + x + ANSI["end"]


def green(x):
    """Color text green using ANSI escape sequences."""
    return ANSI["green"] + x + ANSI["end"]


def setup_logging(level: str):
    logger = logging.getLogger()
    logger.setLevel(logging.getLevelName(level))

    if sys.stderr.isatty():
        logging.addLevelName(logging.WARNING, red(logging.getLevelName(logging.WARNING)))
        logging.addLevelName(logging.ERROR, red(logging.getLevelName(logging.ERROR)))
        logging.addLevelName(logging.INFO, green(logging.getLevelName(logging.INFO)))
        logging.addLevelName(logging.DEBUG, green(logging.getLevelName(logging.DEBUG)))
