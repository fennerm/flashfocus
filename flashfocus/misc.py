"""Utility functions."""
from inspect import getargspec
import os


def list_param(f):
    """List the parameters of a function or method."""
    return [x for x in getargspec(f).args if x != "self"]


def cmd_exists(cmd):
    return any(
        os.access(os.path.join(path, cmd), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )
