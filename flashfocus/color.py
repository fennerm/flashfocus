"""Module for adding color to logging output."""

ANSI = {"green": "\033[92m", "red": "\033[91m", "end": "\033[0m"}


def red(x):
    """Color text red using ANSI escape sequences."""
    return ANSI["red"] + x + ANSI["end"]


def green(x):
    """Color text green using ANSI escape sequences."""
    return ANSI["green"] + x + ANSI["end"]
