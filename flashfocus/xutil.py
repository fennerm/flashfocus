"""Xorg utility code."""
import xcffib
import xcffib.xproto
import xpybutil
import xpybutil.ewmh
import xpybutil.window


def create_message_window():
    """Create a hidden window for sending X client-messages.

    The window's properties can be used to send messages between threads.

    Returns
    -------
    int
        An X-window id.

    """
    setup = xpybutil.conn.get_setup()
    window = xpybutil.conn.generate_id()
    xpybutil.conn.core.CreateWindow(
        depth=setup.roots[0].root_depth,
        wid=window,
        parent=xpybutil.root,
        x=0, y=0, width=1, height=1, border_width=0,
        _class=xcffib.xproto.WindowClass.InputOutput,
        visual=setup.roots[0].root_visual,
        value_mask=xcffib.xproto.CW.EventMask,
        value_list=[xcffib.xproto.EventMask.PropertyChange],
        is_checked=True).check()
    return window


def get_wm_class(window):
    """Get the ID and class of a window

    Returns
    -------
    Tuple[str, str]
        (window id, window class)

    """
    reply = xpybutil.util.get_property_value(
        xpybutil.util.get_property(window, 'WM_CLASS').reply())
    return reply[0], reply[1]


def set_wm_name(window, name):
    """Set the WM_NAME property of a window."""
    xpybutil.conn.core.ChangePropertyChecked(
        xcffib.xproto.PropMode.Replace,
        window,
        xcffib.xproto.Atom.WM_NAME,
        xcffib.xproto.Atom.STRING,
        8,
        len(name),
        name).check()


def set_opacity(window, opacity, checked=True):
    """Set opacity of window.

    If opacity is None, request is ignored.

    """
    if opacity:
        cookie = xpybutil.ewmh.set_wm_window_opacity_checked(window, opacity)
        if checked:

            return cookie.check()
        return cookie


def get_opacity(window):
    """Get the opacity of a window."""
    return xpybutil.ewmh.get_wm_window_opacity(window).reply()


def set_all_window_opacity(opacity):
    """Set all visible window's opacity to `opacity`."""
    for window in xpybutil.ewmh.get_client_list().reply():
        set_opacity(window, opacity, checked=False)
    xpybutil.conn.flush()
