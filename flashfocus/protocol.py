import os


def get_display_protocol():
    if os.environ.get("WAYLAND_DISPLAY"):
        protocol = "wayland"
    else:
        protocol = "x11"
    return protocol


if get_display_protocol() == "wayland":
    from flashfocus.sway import *
else:
    from flashfocus.xutil import *
