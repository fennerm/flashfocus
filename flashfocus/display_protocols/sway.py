import logging
from queue import Queue
from threading import Thread
from typing import List, Optional, Tuple

import i3ipc

from flashfocus.display import WMError, WMMessage, WMMessageType


SWAY = i3ipc.Connection()


class Window:
    def __init__(self, container: i3ipc.i3ipc.Con) -> None:
        self.container = container
        if self.container.id is None:
            raise WMError("Invalid window ID")
        self.id = self.container.id

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        else:
            return self.container.id == other.container.id

    def __ne__(self, other) -> bool:
        if other is None:
            return True
        else:
            return self.id != other.id

    @property
    def wm_class(self) -> Tuple[str, str]:
        """Get the title and class of a window

        Returns
        -------
        (window title, window class)

        """
        return self.container.window_class, self.container.window_instance

    @property
    def opacity(self) -> float:
        # TODO
        pass

    def set_opacity(self, opacity: float) -> None:
        # If opacity is None just silently ignore the request
        self.container.command(f"opacity {opacity}")

    def set_class(self, title: str, class_: str) -> None:
        # TODO
        pass
        # set_wm_class_checked(self.id, title, class_).check()

    def set_name(self, name: str) -> None:
        # TODO
        pass

    def destroy(self) -> None:
        self.container.command("kill")


class DisplayHandler(Thread):
    def __init__(self, queue: Queue) -> None:
        # This is set to True when initialization of the thread is complete and its ready to begin
        # the event loop
        self.ready = False
        super(DisplayHandler, self).__init__()
        self.conn = i3ipc.Connection()
        self.queue = queue

    def run(self) -> None:
        self.conn.on("window::focus", self._handle_focus_shift)
        self.conn.on("window::new", self._handle_new_mapped_window)
        self.ready = True
        self.conn.main()

    def stop(self) -> None:
        self.keep_going = False
        self.conn.main_quit()
        self.join()

    def queue_window(self, window: Window, type: WMMessageType) -> None:
        """Add a window to the queue."""
        self.queue.put(WMMessage(window=window, type=type))

    def _handle_focus_shift(self, _, event: i3ipc.model.Event) -> None:
        if _is_mapped_window(event.container):
            logging.info("Focus shifted to %s", event.container.id)
            self.queue_window(Window(event.container), WMMessageType.FOCUS_SHIFT)

    def _handle_new_mapped_window(self, _, event: i3ipc.model.Event) -> None:
        """Handle a new mapped window event."""
        if _is_mapped_window(event.container):
            logging.info("Window %s mapped...", event.container.id)
            self.queue_window(Window(event.container), WMMessageType.NEW_WINDOW)


def _is_mapped_window(container: i3ipc.con.Con) -> bool:
    return (
        container
        and container.id
        and container.parent.type != "dockarea"
        and container.window_rect.width != 0
    )


def get_focused_window():
    return Window(SWAY.get_tree().find_focused())


def list_mapped_windows(desktop: Optional[int] = None) -> List[Window]:
    windows = list()
    for con in SWAY.get_tree():
        if _is_mapped_window(con):
            windows.append(Window(con))
    return windows


def disconnect_display_conn() -> None:
    SWAY.main_quit()


def get_focused_desktop() -> str:
    return SWAY.get_tree().find_focused().workspace().name


def unset_all_window_opacity() -> None:
    windows = list_mapped_windows()
    for window in windows:
        window.set_opacity(1)
