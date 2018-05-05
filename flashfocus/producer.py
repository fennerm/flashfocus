"""Produce work for the flashfocus server."""
from logging import info
import socket
from threading import Thread

from xcffib import ConnectionException
import xpybutil

from flashfocus.sockets import init_server_socket
from flashfocus.xutil import focus_shifted


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

    def queue_window(self):
        """Add a window to the queue."""
        focused = xpybutil.ewmh.get_active_window().reply()
        self.queue.put(tuple([focused, self.type]))

    def stop(self):
        """Kill the thread."""
        self.keep_going = False
        self.join()


class FocusMonitor(Producer):
    """Queue flashes due to shifts in focus."""
    def __init__(self, queue):
        super(FocusMonitor, self).__init__(queue)
        self.type = 'focus_shift'

    def run(self):
        """Queue focus shift flashes."""
        xpybutil.window.listen(xpybutil.root, 'PropertyChange')

        while self.keep_going:
            try:
                if focus_shifted():
                    info('Focus shifted...')
                    self.queue_window()
            except ConnectionException:
                pass


class ClientMonitor(Producer):
    """Queue flash requests from clients."""
    def __init__(self, queue):
        super(ClientMonitor, self).__init__(queue)
        self.type = 'client_request'
        self.sock = init_server_socket()

    def run(self):
        """Queue client request flashes."""
        while self.keep_going:
            try:
                self.sock.recv(1)
            except socket.timeout:
                pass
            else:
                info('Received a flash request from client...')
                self.queue_window()

    def stop(self):
        super(ClientMonitor, self).stop()
        info('Disconnecting socket...')
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
