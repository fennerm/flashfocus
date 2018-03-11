from logging import info as log
from multiprocessing.dummy import Pool
from socket import (
    AF_UNIX,
    socket,
    SOCK_STREAM,
)
from struct import unpack
from time import sleep

import i3ipc

from i3flash.opacity import (
    delete_opacity_property,
    set_opacity,
)


class FlashServer(object):
    def __init__(self, opacity, time, socketfile='/tmp/i3flash_socket'):
        # TODO: Check for compton and issue warning
        self.opacity = opacity
        self.time = time
        # self.threads = Pool(2)

        # log('Establishing connection with i3...')
        # self.i3 = i3ipc.Connection()
        # log('Connection established')

        self.focused_window = self.i3.get_tree().find_focused().window

        log('Initializing a socket at %s', socketfile)
        self.socket = socket(AF_UNIX, SOCK_STREAM)
        self.socket.bind(socketfile)
        log('Socket initialized')

    def run(self):
        self.monitor_focus()
        # self.threads.apply_async(self.monitor_focus)
        # self.threads.apply_async(self.monitor_client)

    def flash_window(self, x_window_id):
        '''Briefly decrease the opacity of a Xorg window'''
        log('Flashing window %s', str(x_window_id))
        set_opacity(x_window_id, opacity=self.opacity)

        log('Waiting %ss...', self.time)
        sleep(self.time)

        # Setting opacity to the max wouldn't work if the window has the
        # _NET_WM_OPAQUE_REGION defined, so we just delete the
        # _NET_WM_WINDOW_OPACITY property to return to the default
        delete_opacity_property(x_window_id)

    def monitor_focus(self):
        '''Wait for changes in focus and flash windows'''
        def on_window_focus(_, event):
            '''Change in focus hook'''
            x_window_id = str(event.container.window)
            self.flash_window(x_window_id)
            self.focused_window = x_window_id
            log('Waiting for focus shift...')

        self.i3.on('window::focus', on_window_focus)
        log('Waiting for focus shift...')
        self.i3.main()

    # def monitor_client(self):
    #     self.socket.listen(True)
    #     connection, _ = self.socket.accept()
    #     log('Waiting for client requests...')
    #     while True:
    #         data = connection.recv(8)
    #         if data == b'':
    #             raise RuntimeError('The client shutdown unexpectedly')
    #         log('Received a request from the focus client...')
    #         request = unpack('<L', data)[0]
    #         if request == 1:
    #             log('Flashing current window at client\'s request...')
    #             self.flash_window(self.focused_window)
    #         else:
    #             raise RuntimeError('Received an unexpected response from the '
    #                                'client \n'
    #                                'Expected: 1 or None \n'
    #                                'Received: {}'.format(str(request)))
