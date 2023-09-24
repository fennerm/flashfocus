import re
from subprocess import CalledProcessError, check_output
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


def find_process(process_name: str) -> bool:
    """Check if a process is running by name."""
    try:
        check_output(["pidof", process_name])
    except CalledProcessError:
        exists = False
    else:
        exists = True
    return exists
