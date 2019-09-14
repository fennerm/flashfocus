"""Compatibility module for abstracting across display protocols."""
from enum import auto, Enum
import logging
import os

from flashfocus.errors import UnsupportedWM
from flashfocus.util import find_process


class DisplayProtocol(Enum):
    SWAY = auto()
    WAYLAND = auto()
    X11 = auto()


def get_display_protocol() -> DisplayProtocol:
    if find_process("sway"):
        protocol = DisplayProtocol.SWAY
    elif os.environ.get("WAYLAND_DISPLAY"):
        protocol = DisplayProtocol.WAYLAND
    else:
        protocol = DisplayProtocol.X11
    return protocol


_display_protocol = get_display_protocol()

if _display_protocol is DisplayProtocol.SWAY:
    logging.info("Detected display protocol: wayland - sway")
    from flashfocus.display_protocols.sway import (
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_workspace as get_focused_workspace,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        Window as Window,
    )
elif _display_protocol is DisplayProtocol.WAYLAND:
    logging.info("Detected display protocol: wayland - other")
    raise UnsupportedWM("This window manager is not supported yet.")
else:
    logging.info("Detected display protocol: X11")
    from flashfocus.display_protocols.x11 import (  # noqa: F401
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_workspace as get_focused_workspace,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        Window as Window,
    )
