"""Compatibility module for abstracting across display protocols."""
from enum import auto, Enum
import os


class DisplayProtocol(Enum):
    WAYLAND = auto()
    X11 = auto()


def get_display_protocol() -> DisplayProtocol:
    if os.environ.get("WAYLAND_DISPLAY"):
        protocol = DisplayProtocol.WAYLAND
    else:
        protocol = DisplayProtocol.X11
    return protocol


# The imports here represent the minimal set of utilities which are required for flashfocus to use a
# display backend.
if get_display_protocol() is DisplayProtocol.WAYLAND:
    from flashfocus.display_protocols.sway import (
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_workspace as get_focused_workspace,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        Window as Window,
    )
else:
    from flashfocus.display_protocols.x11 import (  # noqa: F401
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_workspace as get_focused_workspace,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        Window as Window,
    )
