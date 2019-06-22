"""Produce work for the flashfocus server."""
from threading import Thread


class Producer(Thread):
    """Queue windows to be handled by the `FlashServer`.

    Parameters
    ----------
    queue: queue.Queue
        A queue which is shared among `Producer` instances

    """

    def __init__(self, queue):
        super(Producer, self).__init__()
        self.queue = queue
        self.keep_going = True

    def queue_window(self, window, type):
        """Add a window to the queue."""
        self.queue.put(tuple([window, type]))

    def stop(self):
        self.keep_going = False
        self.join()
