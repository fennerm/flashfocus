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

if _display_protocol is DisplayProtocol.SWAY:
    logging.info("Detected display protocol: wayland - sway")
    from flashfocus.display_protocols.sway import \
        DisplayHandler as DisplayHandler
    from flashfocus.display_protocols.sway import Window as Window
    from flashfocus.display_protocols.sway import \
        disconnect_display_conn as disconnect_display_conn
    from flashfocus.display_protocols.sway import \
        get_focused_window as get_focused_window
    from flashfocus.display_protocols.sway import \
        get_focused_workspace as get_focused_workspace
    from flashfocus.display_protocols.sway import \
        list_mapped_windows as list_mapped_windows
elif _display_protocol is DisplayProtocol.WAYLAND:
    logging.info("Detected display protocol: wayland - other")
    raise UnsupportedWM("This window manager is not supported yet.")
else:
    logging.info("Detected display protocol: X11")
    from flashfocus.display_protocols.x11 import \
        DisplayHandler as DisplayHandler
    from flashfocus.display_protocols.x11 import Window as Window
    from flashfocus.display_protocols.x11 import \
        disconnect_display_conn as disconnect_display_conn  # noqa: F401
    from flashfocus.display_protocols.x11 import \
        get_focused_window as get_focused_window
    from flashfocus.display_protocols.x11 import \
        get_focused_workspace as get_focused_workspace
    from flashfocus.display_protocols.x11 import \
        list_mapped_windows as list_mapped_windows
