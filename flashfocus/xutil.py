"""Xorg utility code."""
import struct

from xcffib.xproto import CW, EventMask, WindowClass
from xpybutil import conn, root
from xpybutil.ewmh import (
    get_current_desktop,
    get_wm_desktop,
    set_wm_window_opacity_checked,
)
from xpybutil.icccm import get_wm_class as _get_wm_class
import xpybutil.window


class WMError(ValueError):
    """An error related to an Xorg window."""

    pass


def create_message_window():
    """Create a hidden window for sending X client-messages.

    The window's properties can be used to send messages between threads.

    Returns
    -------
    int
        An X-window id.

    """
    setup = conn.get_setup()
    window = conn.generate_id()
    conn.core.CreateWindow(
        depth=setup.roots[0].root_depth,
        wid=window,
        parent=root,
        x=0,
        y=0,
        width=1,
        height=1,
        border_width=0,
        _class=WindowClass.InputOutput,
        visual=setup.roots[0].root_visual,
        value_mask=CW.EventMask,
        value_list=[EventMask.PropertyChange],
        is_checked=True,
    ).check()
    return window


def get_wm_class(window):
    """Get the ID and class of a window

    Returns
    -------
    Tuple[str, str]
        (window id, window class)

    """
    try:
        reply = _get_wm_class(window).reply()
    except struct.error:
        raise WMError("Invalid window: %s", window)
    try:
        return reply[0], reply[1]
    except TypeError:
        return None, None


def set_opacity(window, opacity, checked=True):
    """Set opacity of window.

    If opacity is None, request is ignored.

    """
    if opacity:
        cookie = set_wm_window_opacity_checked(window, opacity)
        if checked:
            return cookie.check()
        return cookie


def destroy_window(window):
    conn.core.DestroyWindow(window, True).check()


def count_windows(desktop):
    cookies = [get_wm_desktop(window) for window in list_mapped_windows()]
    window_desktops = [cookie.reply() for cookie in cookies]
    return sum([d == desktop for d in window_desktops])


def list_mapped_windows(desktop=None):
    mapped_windows = xpybutil.ewmh.get_client_list().reply()
    if mapped_windows is None:
        return []
    else:
        return mapped_windows


def get_current_desktop():
    return xpybutil.ewmh.get_current_desktop().reply()


def unset_all_window_opacity():
    """Unset the opacity of all mapped windows."""
    cookies = [
        set_opacity(window, 1, checked=False) for window in list_mapped_windows()
    ]
    xpybutil.conn.flush()
    for cookie in cookies:
        cookie.check()
