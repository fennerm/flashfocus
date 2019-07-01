"""Xorg utility code."""
import logging
from queue import Queue
import struct
from threading import Thread
from typing import List, Optional, Tuple, Union

from xcffib.xproto import (
    CreateNotifyEvent,
    CW,
    EventMask,
    PropertyNotifyEvent,
    WindowClass,
    WindowError,
)
from xpybutil import conn, root
from xpybutil.ewmh import (
    get_active_window,
    get_client_list,
    get_current_desktop,
    get_wm_desktop,
    get_wm_window_opacity,
    set_wm_window_opacity_checked,
)
from xpybutil.icccm import get_wm_class, set_wm_class_checked, set_wm_name_checked
import xpybutil.window
from xpybutil.util import get_atom_name

from flashfocus.display import WMError, WMMessage, WMMessageType


Event = Union[CreateNotifyEvent, PropertyNotifyEvent]


class Window:
    def __init__(self, window_id: int) -> None:
        if window_id is None:
            raise WMError("Undefined window")
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
        except (struct.error, WindowError) as e:
            raise WMError("Invalid window: %s", self.id) from e
        try:
            return reply[0], reply[1]
        except TypeError:
            return None, None

    @property
    def opacity(self) -> float:
        return get_wm_window_opacity(self.id).reply()

    def set_opacity(self, opacity: Optional[float]) -> None:
        # If opacity is None just silently ignore the request
        if opacity:
            cookie = set_wm_window_opacity_checked(self.id, opacity)
            cookie.check()

    def set_class(self, title: str, class_: str) -> None:
        set_wm_class_checked(self.id, title, class_).check()

    def set_name(self, name: str) -> None:
        set_wm_name_checked(self.id, name).check()

    def destroy(self) -> None:
        try:
            conn.core.DestroyWindow(self.id, True).check()
        except WindowError as e:
            raise WMError from e


def _create_message_window() -> Window:
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

    def __init__(self, queue: Queue) -> None:
        # This is set to True when initialization of the thread is complete and its ready to begin
        # the event loop
        self.ready = False

        super(DisplayHandler, self).__init__()

        # Queue of messages to be handled by the flash server
        self.queue: Queue = queue

        # This property is set by the server during shutdown and signals that the display handler
        # should disconnect from XCB
        self.keep_going: bool = True

        # In order to interrupt the event loop we need to map a special message-passing window.
        # When it comes time to exit we set the name of the window to 'KILL'. This is then
        # picked up as an event in the event loop. See https://xcb.freedesktop.org/tutorial/events/
        self.message_window: Window = _create_message_window()

    def run(self) -> None:
        # PropertyChange is for detecting changes in focus
        # SubstructureNotify is for detecting new mapped windows
        xpybutil.window.listen(xpybutil.root, "PropertyChange", "SubstructureNotify")

        # Also listen to property changes in the message window
        xpybutil.window.listen(self.message_window.id, "PropertyChange")

        self.ready = True
        while self.keep_going:
            event = conn.wait_for_event()
            if isinstance(event, PropertyNotifyEvent):
                self._handle_property_change(event)
            elif isinstance(event, CreateNotifyEvent):
                self._handle_new_mapped_window(event)

    def stop(self) -> None:
        set_wm_name_checked(self.message_window.id, "KILL").check()
        self.keep_going = False
        self.join()
        self.message_window.destroy()

    def queue_window(self, window: Window, type: WMMessageType) -> None:
        """Add a window to the queue."""
        self.queue.put(WMMessage(window=window, type=type))

    def _handle_new_mapped_window(self, event: Event) -> None:
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

    def _handle_property_change(self, event: Event) -> None:
        """Handle a property change on a watched window."""
        atom_name = get_atom_name(event.atom)
        if atom_name == "_NET_ACTIVE_WINDOW":
            focused_window = get_focused_window()
            logging.info(f"Focus shifted to {focused_window.id}")
            self.queue_window(focused_window, WMMessageType.FOCUS_SHIFT)
        elif atom_name == "WM_NAME" and event.window == self.message_window.id:
            # Received kill signal from server -> terminate the thread
            self.keep_going = False


def get_focused_window() -> Window:
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


def unset_all_window_opacity() -> None:
    """Unset the opacity of all mapped windows."""
    for window in list_mapped_windows():
        window.set_opacity(1)


def disconnect_display_conn() -> None:
    conn.disconnect()
