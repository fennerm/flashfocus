import re
from typing import Pattern


def match_regex(regex: Pattern, target: str) -> bool:
    try:
        return bool(re.match(regex, target))
    except TypeError:
        # For our purposes, target is probably None
        return False


def indent(n: int) -> str:
    """Return `n` indents."""
    return "  " * n
