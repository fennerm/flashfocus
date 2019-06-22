import logging

import i3ipc

from flashfocus.producer import Producer

SWAY = i3ipc.Connection()


class DisplayHandler(Producer):
    def __init__(self, queue):
        super(DisplayHandler, self).__init__(queue)
        self.type = "focus_shift"
        self.conn = i3ipc.Connection()

    def run(self):
        self.conn.on("window::focus", self._handle_focus_shift)
        self.conn.on("window::new", self._handle_new_mapped_window)
        self.conn.main()

    def stop(self):
        self.conn.main_quit()
        super(DisplayHandler, self).stop()

    def _handle_focus_shift(self, _, event):
        logging.info("Focus shifted to %s", event.container.window)
        self.queue_window(event.container.window, "focus_shift")

    def _handle_new_mapped_window(self, _, event):
        """Handle a new mapped window event."""
        logging.info("Window %s mapped...", event.container.window)
        self.queue_window(event.container.window, "new_window")
