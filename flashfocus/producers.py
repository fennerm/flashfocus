from flashfocus.sockets import init_server_socket
import flashfocus.xutil as xutil


def handle_focus_shifts(self, task_queue):
    xutil.start_watching_properties(xutil.ROOT_WINDOW)
    while True:
        xutil.wait_for_focus_shift()
        focused = xutil.request_focus().unpack()
        task_queue.put(tuple(focused, 'focus_shift'))


def handle_client_requests(self):
    try:
        sock = init_server_socket()
        while True:
            client_connection = sock.accept()[0]
            client_connection.recv(1)
            focused = xutil.request_focus().unpack()
            self.tasks.put(tuple(focused, 'client_request'))
    finally:
        sock.close()
