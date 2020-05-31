"""Xorg utility code.

All submodules in flashfocus.display_protocols are expected to contain a minimal set of
functions/classes for abstracting across various display protocols. See list in flashfocus.compat

"""
import functools
import logging
from queue import Queue
import struct
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Union

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
    get_wm_state,
    get_wm_window_opacity,
    set_wm_window_opacity_checked,
)
from xpybutil.icccm import get_wm_class, set_wm_class_checked, set_wm_name_checked
import xpybutil.window
from xpybutil.util import get_atom_name, PropertyCookieSingle

from flashfocus.display import WMEvent, WMEventType
from flashfocus.errors import WMError
from flashfocus.util import match_regex


Event = Union[CreateNotifyEvent, PropertyNotifyEvent]


def ignore_window_error(function: Callable) -> Callable:
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except WindowError:
            pass

    return wrapper


class Window:
    def __init__(self, window_id: int) -> None:
        """Represents an Xorg window.

        Parameters
        ----------
        window_id
            The XORG window ID

        Attributes
        ----------
        id
            The XORG window ID
        """
        if window_id is None:
            raise WMError("Undefined window")
        self.id = window_id
        self._properties: Dict = dict()

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            raise TypeError("Arguments must be of the same type")
        return self.id == other.id

    def __ne__(self, other) -> bool:
        if type(self) != type(other):
            raise TypeError("Arguments must be of the same type")
        return self.id != other.id

    @property
    def properties(self) -> Dict:
        """Get a dictionary with the window class and instance."""
        # Properties are cached after the first call to this function and so might not necessarily
        # be correct if the properties are changed between calls. This is acceptable for our
        # purposes because Windows are short-lived objects.
        if not self._properties:
            try:
                reply = get_wm_class(self.id).reply()
            except (struct.error, WindowError) as e:
                raise WMError("Invalid window: %s", self.id) from e
            try:
                self._properties = {"window_id": reply[0], "window_class": reply[1]}
            except TypeError:
                pass
        return self._properties

    def match(self, criteria: Dict) -> bool:
        """Determine whether the window matches a set of criteria.

        Parameters
        ----------
        criteria
            Dictionary of regexes of the form {PROPERTY: REGEX} e.g {"window_id": r"termite"}

        """
        if not criteria.get("window_id") and not criteria.get("window_class"):
            return True
        for prop in ["window_id", "window_class"]:
            # https://github.com/fennerm/flashfocus/issues/43
            # I'm not 100 % sure but this issue seems to indicate that in some WMs a window might
            # have an ID but not a class.
            if (
                criteria.get(prop)
                and self.properties.get(prop)
                and not match_regex(criteria[prop], self.properties[prop])
            ):
                return False
        return True

    @property
    def opacity(self) -> float:
        return get_wm_window_opacity(self.id).reply()

    @ignore_window_error
    def set_opacity(self, opacity: Optional[float]) -> None:
        # If opacity is None just silently ignore the request
        if opacity is not None:
            cookie = set_wm_window_opacity_checked(self.id, opacity)
            cookie.check()

    @ignore_window_error
    def set_class(self, title: str, class_: str) -> None:
        set_wm_class_checked(self.id, title, class_).check()

    @ignore_window_error
    def set_name(self, name: str) -> None:
        set_wm_name_checked(self.id, name).check()

    @ignore_window_error
    def destroy(self) -> None:
        try:
            conn.core.DestroyWindow(self.id, True).check()
        except WindowError as e:
            raise WMError from e

    @ignore_window_error
    def is_fullscreen(self) -> bool:
        wm_states = get_wm_state(self.id).reply()
        # wm_states might be null in some WMs - #29
        if wm_states:
            for wm_state in wm_states:
                if get_atom_name(wm_state) == "_NET_WM_STATE_FULLSCREEN":
                    return True
        return False


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

    def queue_window(self, window: Window, event_type: WMEventType) -> None:
        self.queue.put(WMEvent(window=window, event_type=event_type))

    def _handle_new_mapped_window(self, event: Event) -> None:
        logging.debug(f"Window {event.window} mapped...")
        if event.window is not None:
            window = Window(event.window)
            # Check that window is visible so that we don't accidentally set
            # opacity of windows which are not for display. Without this step
            # window opacity can become frozen and stop responding to flashes.
            if window in list_mapped_windows():
                self.queue_window(window, WMEventType.NEW_WINDOW)
            else:
                logging.debug(f"Window {window.id} is not visible, ignoring...")

    def _handle_property_change(self, event: Event) -> None:
        """Handle a property change on a watched window."""
        atom_name = get_atom_name(event.atom)
        if atom_name == "_NET_ACTIVE_WINDOW":
            focused_window = get_focused_window()
            if focused_window is not None:
                logging.debug(f"Focus shifted to {focused_window.id}")
                self.queue_window(focused_window, WMEventType.FOCUS_SHIFT)
        elif atom_name == "WM_NAME" and event.window == self.message_window.id:
            # Received kill signal from server -> terminate the thread
            self.keep_going = False


@ignore_window_error
def get_focused_window() -> Optional[Window]:
    window_id = get_active_window().reply()
    if window_id is not None:
        return Window(window_id)
    else:
        return None


def _try_unwrap(cookie: PropertyCookieSingle) -> Optional[Any]:
    """Try reading a reply from the X server, ignoring any errors encountered."""
    try:
        return cookie.reply()
    except WindowError:
        return None


@ignore_window_error
def list_mapped_windows(workspace: Optional[int] = None) -> List[Window]:
    mapped_window_ids = get_client_list().reply()
    if mapped_window_ids is None:
        mapped_window_ids = list()

    mapped_windows = [Window(wid) for wid in mapped_window_ids if wid is not None]
    if workspace is not None:
        cookies = [get_wm_desktop(wid) for wid in mapped_window_ids]
        workspaces = [_try_unwrap(cookie) for cookie in cookies]
        mapped_windows = [win for win, ws in zip(mapped_windows, workspaces) if ws == workspace]
    return mapped_windows


@ignore_window_error
def get_focused_workspace() -> int:
    return get_current_desktop().reply()


@ignore_window_error
def disconnect_display_conn() -> None:
    conn.disconnect()
