"""Xorg utility code."""
import logging
import struct
from threading import Thread
from typing import List, Optional, Tuple

from xcffib.xproto import CreateNotifyEvent, CW, EventMask, PropertyNotifyEvent, WindowClass
from xpybutil import conn, root
from xpybutil.ewmh import (
    get_active_window,
    get_client_list,
    get_current_desktop,
    get_wm_desktop,
    set_wm_window_opacity_checked,
)
from xpybutil.icccm import get_wm_class, set_wm_name_checked
import xpybutil.window
from xpybutil.util import get_atom_name

from flashfocus.display import WMError, WMMessage, WMMessageType


class Window:
    def __init__(self, window_id):
        self.id = window_id

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        else:
            return self.id == other.id

    def __ne__(self, other) -> bool:
        if other is None:
            return True
        else:
            return self.id != other.id

    @property
    def wm_class(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the title and class of a window

        Returns
        -------
        (window title, window class)

        """
        try:
            reply = get_wm_class(self.id).reply()
        except struct.error:
            raise WMError("Invalid window: %s", self.id)
        try:
            return reply[0], reply[1]
        except TypeError:
            return None, None

    def set_opacity(self, opacity: Optional[float]) -> None:
        # If opacity is None just silently ignore the request
        if opacity:
            cookie = set_wm_window_opacity_checked(self.id, opacity)
            cookie.check()

    def destroy(self) -> None:
        conn.core.DestroyWindow(self.id, True).check()


def _create_message_window():
    """Create a hidden window for sending X client-messages.

    The window's properties can be used to send messages between threads.

    Returns
    -------
    int
        An X-window id.

    """
    setup = conn.get_setup()
    window_id = conn.generate_id()
    conn.core.CreateWindow(
        depth=setup.roots[0].root_depth,
        wid=window_id,
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
    return Window(window_id)


class DisplayHandler(Thread):
    """Parse events from the X-server and pass them on to FlashServer"""

    def __init__(self, queue):
        super(DisplayHandler, self).__init__()
        self.queue = queue
        self.keep_going = True
        self.message_window: Window = _create_message_window()

    def run(self):
        xpybutil.window.listen(xpybutil.root, "PropertyChange", "SubstructureNotify")
        xpybutil.window.listen(self.message_window.id, "PropertyChange")
        while self.keep_going:
            event = conn.wait_for_event()
            if isinstance(event, PropertyNotifyEvent):
                self._handle_property_change(event)
            elif isinstance(event, CreateNotifyEvent):
                self._handle_new_mapped_window(event)

    def stop(self):
        set_wm_name_checked(self.message_window.id, "KILL").check()
        self.keep_going = False
        self.join()
        self.message_window.destroy()

    def queue_window(self, window: Window, type: WMMessageType):
        """Add a window to the queue."""
        self.queue.put(WMMessage(window=window, type=type))

    def _handle_new_mapped_window(self, event):
        """Handle a new mapped window event."""
        logging.info(f"Window {event.window} mapped...")
        # Check that window is visible so that we don't accidentally set
        # opacity of windows which are not for display. Without this step
        # window opacity can become frozen and stop responding to flashes.
        window = Window(event.window)
        if window in list_mapped_windows():
            self.queue_window(window, WMMessageType.NEW_WINDOW)
        else:
            logging.info(f"Window {window.id} is not visible, ignoring...")

    def _handle_property_change(self, event):
        """Handle a property change on a watched window."""
        atom_name = get_atom_name(event.atom)
        if atom_name == "_NET_ACTIVE_WINDOW":
            focused_window = get_focused_window()
            logging.info(f"Focus shifted to {focused_window.id}")
            self.queue_window(focused_window, WMMessageType.FOCUS_SHIFT)
        elif atom_name == "WM_NAME" and event.window == self.message_window.id:
            # Received kill signal from server -> terminate the thread
            self.keep_going = False


def get_focused_window():
    return Window(get_active_window().reply())


def list_mapped_windows(desktop: Optional[int] = None) -> List[Window]:
    mapped_window_ids = get_client_list().reply()
    if mapped_window_ids is None:
        mapped_window_ids = []
    mapped_windows = [Window(window_id) for window_id in mapped_window_ids]

    if desktop is not None:
        cookies = [get_wm_desktop(window.id) for window in list_mapped_windows()]
        window_desktops = [cookie.reply() for cookie in cookies]
        mapped_windows = [win for win, dt in zip(mapped_windows, window_desktops) if dt == desktop]
    return mapped_windows


def get_focused_desktop() -> int:
    return get_current_desktop().reply()


def unset_all_window_opacity():
    """Unset the opacity of all mapped windows."""
    for window in list_mapped_windows():
        window.set_opacity(1)


def disconnect_display_conn():
    conn.disconnect()
