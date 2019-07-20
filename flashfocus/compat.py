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


if get_display_protocol() is DisplayProtocol.WAYLAND:
    from flashfocus.display_protocols.sway import (
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_desktop as get_focused_desktop,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        unset_all_window_opacity as unset_all_window_opacity,
        Window as Window,
    )
else:
    from flashfocus.display_protocols.x11 import (
        disconnect_display_conn as disconnect_display_conn,
        DisplayHandler as DisplayHandler,
        get_focused_desktop as get_focused_desktop,
        get_focused_window as get_focused_window,
        list_mapped_windows as list_mapped_windows,
        unset_all_window_opacity as unset_all_window_opacity,
        Window as Window,
    )
