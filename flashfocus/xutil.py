"""Xorg utility code."""
import logging
import struct

from xcffib.xproto import CreateNotifyEvent, CW, EventMask, PropertyNotifyEvent, WindowClass
from xpybutil import conn, root
from xpybutil.ewmh import get_current_desktop, get_wm_desktop, set_wm_window_opacity_checked
from xpybutil.icccm import get_wm_class as _get_wm_class, set_wm_name_checked
from xpybtuil.util import get_atom_name
import xpybutil.window

from flashfocus.producer import Producer


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


class DisplayHandler(Producer):
    """Parse events from the X-server and pass them on to FlashServer"""

    def __init__(self, queue):
        super(DisplayHandler, self).__init__(queue)
        self.type = "focus_shift"
        self.message_window = create_message_window()

    def run(self):
        while self.keep_going:
            event = xpybutil.conn.wait_for_event()
            if isinstance(event, PropertyNotifyEvent):
                self._handle_property_change(event)
            elif isinstance(event, CreateNotifyEvent):
                self._handle_new_mapped_window(event)

    def stop(self):
        set_wm_name_checked(self.message_window, "KILL").check()
        super(DisplayHandler, self).stop()
        destroy_window(self.message_window)

    def _handle_new_mapped_window(self, event):
        """Handle a new mapped window event."""
        logging.info("Window %s mapped...", event.window)
        # Check that window is visible so that we don't accidentally set
        # opacity of windows which are not for display. Without this step
        # window opacity can become frozen and stop responding to flashes.
        if event.window in list_mapped_windows():
            self.queue_window(event.window, "new_window")
        else:
            logging.info("Window %s is not visible, ignoring...", event.window)

    def _handle_property_change(self, event):
        """Handle a property change on a watched window."""
        atom_name = get_atom_name(event.atom)
        if atom_name == "_NET_ACTIVE_WINDOW":
            focused_window = get_active_window().reply()
            logging.info("Focus shifted to %s", focused_window)
            self.queue_window(focused_window, "focus_shift")
        elif atom_name == "WM_NAME" and event.window == self.message_window:
            # Received kill signal from server -> terminate the thread
            self.keep_going = False


class Window:
    def __init__(self, window_id):
        self.uid = window_id

    @property
    def class_(self):
        """Get the ID and class of a window

        Returns
        -------
        Tuple[str, str]
            (window id, window class)

        """
        pass


def get_wm_class(window):
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
    cookies = [set_opacity(window, 1, checked=False) for window in list_mapped_windows()]
    xpybutil.conn.flush()
    for cookie in cookies:
        cookie.check()
