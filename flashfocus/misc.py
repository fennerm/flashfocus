"""Utility functions."""
from inspect import getargspec


def list_param(f):
    """List the parameters of a function or method."""
    return [x for x in getargspec(f).args if x != "self"]
