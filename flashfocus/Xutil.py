'''Manipulate Xorg window opacity'''
from __future__ import division

from struct import pack

import xcffib as xcb
import xcffib.xproto as xproto

# 0xffffffff
MAX_OPACITY = 4294967295


def get_opacity_atom(xcb_connection):
    '''Get the _NET_WM_WINDOW_OPACITY atom from X'''
    atom_bytes = '_NET_WM_WINDOW_OPACITY'.encode('ascii')
    wm_opacity_atom_cookie = xcb_connection.core.InternAtom(
        False, len(atom_bytes), atom_bytes)
    wm_opacity_atom = wm_opacity_atom_cookie.reply().atom
    return wm_opacity_atom


CONN = xcb.connect()
ROOT = CONN.get_setup().roots[0].root
WM_OPACITY_ATOM = get_opacity_atom(CONN)


class OpacityRequest:
    '''A request for the current _NET_WM_WINDOW_OPACITY property of a window'''
    def __init__(self, window):
        self.cookie = CONN.core.GetProperty(
            delete=False,
            window=window,
            property=WM_OPACITY_ATOM,
            type=xproto.GetPropertyType.Any,
            long_offset=0,
            long_length=63
        )
        self.response = None

    def unpack(self):
        '''
        Returns
        -------
        float
            Opacity as a decimal. Returns None if _NET_WM_WINDOW_OPACITY is
            unset.
        '''
        try:
            reply = self.cookie.reply().value.to_atoms()[0]
            self.response = int(reply) / MAX_OPACITY
        except IndexError:
            self.response = None
        return self.response


class FocusRequest:
    '''A request for the currently focused window'''
    def __init__(self):
        self.cookie = CONN.core.GetInputFocus()
        self.response = None

    def unpack(self):
        self.response = int(self.cookie.reply().focus)
        return self.response


def request_opacity(window):
    '''Request the opacity of a window'''
    return OpacityRequest(window)


def request_focus():
    '''Request the currently focused window'''
    return FocusRequest()


def set_opacity(window, opacity):
    '''Set the _NET_WM_WINDOW_OPACITY property of a window

    Parameters
    ----------
    window: int
        The X id of a window
    opacity: float
        Opacity as a decimal < 1
    '''
    data = pack('I', int(opacity * MAX_OPACITY))
    # Add argument names
    void_cookie = CONN.core.ChangePropertyChecked(
        mode=xproto.PropMode.Replace,
        window=window,
        property=WM_OPACITY_ATOM,
        type=xproto.Atom.CARDINAL,
        format=32,
        data_len=1,
        data=data)
    void_cookie.check()
