'''Manipulate Xorg window opacity'''
from __future__ import division

from struct import pack

import xcffib
import xcffib.xproto as xproto

# 0xffffffff
MAX_OPACITY = 4294967295


def intern_atom(xcb_connection, atom_name):
    '''Get the id of an atom from X given its name'''
    atom_bytes = atom_name.encode('ascii')
    cookie = xcb_connection.core.InternAtom(
        False, len(atom_bytes), atom_bytes)
    atom = cookie.reply().atom
    return atom


CONN = xcffib.connect()
ROOT = CONN.get_setup().roots[0].root
WM_OPACITY_ATOM = intern_atom(CONN, '_NET_WM_WINDOW_OPACITY')
ACTIVE_WINDOW_ATOM = intern_atom(CONN, '_NET_ACTIVE_WINDOW')


class OpacityCookie(object):
    '''A request for the current _NET_WM_WINDOW_OPACITY property of a window'''
    def __init__(self, cookie):
        self.cookie = cookie
        self.response = None

    def unpack(self):
        '''Parse the response from the X server

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


class ActiveWindowCookie(object):
    '''A request for the currently focused window'''
    def __init__(self, cookie):
        self.cookie = cookie
        self.response = None

    def unpack(self):
        '''Parse the response from the X server

        Returns
        -------
        int
            The X window id of the active window
        '''
        self.response = int(self.cookie.reply().focus)

        return self.response


def request_opacity(window):
    '''Request the opacity of a window'''
    cookie = CONN.core.GetProperty(
        delete=False,
        window=window,
        property=WM_OPACITY_ATOM,
        type=xproto.GetPropertyType.Any,
        long_offset=0,
        long_length=63
    )
    return OpacityCookie(cookie)


def request_focus():
    '''Request the currently focused window'''
    cookie = CONN.core.GetInputFocus()
    return ActiveWindowCookie(cookie)


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


def delete_opacity(window):
    '''Delete the _NET_WM_WINDOW_OPACITY property from a window'''
    cookie = CONN.core.GetProperty(
        delete=True,
        window=window,
        property=WM_OPACITY_ATOM,
        type=xproto.GetPropertyType.Any,
        long_offset=0,
        long_length=63
    )
    cookie.reply()


def watch_properties(xcb_connection):
    mask = getattr(xproto.EventMask, 'PropertyChange')
    xcb_connection.core.ChangeWindowAttributesChecked(
        ROOT,
        xproto.CW.EventMask,
        [mask]).check()
