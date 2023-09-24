"""Compatibility module for abstracting across display protocols."""
import logging
import os
from enum import Enum, auto

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

# pylint: disable=unused-import
if _display_protocol is DisplayProtocol.SWAY:
    logging.info("Detected display protocol: wayland - sway")
    from flashfocus.display_protocols.sway import (  # noqa: F401
        DisplayHandler,
        Window,
        disconnect_display_conn,
        get_focused_window,
        get_focused_workspace,
        get_workspace,
        list_mapped_windows,
    )
elif _display_protocol is DisplayProtocol.WAYLAND:
    logging.info("Detected display protocol: wayland - other")
    raise UnsupportedWM("This window manager is not supported yet.")
else:
    logging.info("Detected display protocol: X11")
    from flashfocus.display_protocols.x11 import (  # type: ignore # noqa: F401
        DisplayHandler,
        Window,
        disconnect_display_conn,
        get_focused_window,
        get_focused_workspace,
        get_workspace,
        list_mapped_windows,
    )
