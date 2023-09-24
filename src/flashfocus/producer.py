from queue import Queue
from threading import Thread

from flashfocus.display import BaseWindow, WMEvent, WMEventType


class ProducerThread(Thread):
    """Base class for a thread which produces events to be handled by the flashfocus server.

    Attributes
    ----------
    ready: bool
        True if thread is fully initialized and ready to process events
    queue: Queue
        Queue of WMEvents which require processing.
    keep_going: bool
        If this attribute is set to False the thread will attempt to shutdown.

    """

    def __init__(self, queue: Queue) -> None:
        super().__init__()
        # This is set to True when initialization of the thread is complete and its ready to begin
        # the event loop
        self.ready = False

        # Queue of messages to be handled by the flash server
        self.queue = queue

        # This property is set by the server during shutdown and signals that the display handler
        # should disconnect from XCB
        self.keep_going = True

    def queue_window(self, window: BaseWindow, event_type: WMEventType) -> None:
        """Add a window to the queue."""
        self.queue.put(WMEvent(window=window, event_type=event_type))

    def stop(self) -> None:
        self.keep_going = False
        self.join()
