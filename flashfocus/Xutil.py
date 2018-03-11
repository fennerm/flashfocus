'''Manipulate Xorg window opacity'''
from __future__ import division

from struct import pack
from subprocess import (
    call,
    check_output,
)
import xcffib as xcb
import xcffib.xproto as xproto

# 0xffffffff
MAX_OPACITY = 4294967295

# def get_opacity(x_window_id):
#     '''Get the opacity of a window from its Xorg window id'''
#     opacity = check_output(
#         'xprop -id ' + str(x_window_id) +
#         ' | grep _NET_WM_WINDOW_OPACITY | sed -ne "s/^.*= //p"', shell=True)
#     opacity = opacity.decode('utf-8').strip()
#     return opacity


def get_opacity_atom(xcb_connection):
    atom_bytes = '_NET_WM_WINDOW_OPACITY'.encode('ascii')
    wm_opacity_atom_cookie = xcb_connection.core.InternAtom(
        False, len(atom_bytes), atom_bytes)
    wm_opacity_atom = wm_opacity_atom_cookie.reply().atom
    return wm_opacity_atom


CONN = xcb.connect()
WM_OPACITY_ATOM = get_opacity_atom(CONN)

def request_opacity(x_window_id):
    wm_opacity_cookie = CONN.core.GetProperty(
        delete=False,
        window=x_window_id,
        property=WM_OPACITY_ATOM,
        type=xproto.GetPropertyType.Any,
        long_offset=0,
        long_length=63
    )
    return wm_opacity_cookie

def unpack_cookie(opacity_cookie):
    try:
        reply = opacity_cookie.reply().value.to_atoms()[0]
        opacity = int(reply) / MAX_OPACITY
    except IndexError:
        opacity = 1
    return opacity

def set_opacity(x_window_id, opacity):
    data = pack('I', int(opacity * MAX_OPACITY))
    # Add argument names
    void_cookie = CONN.core.ChangeProperty(
        mode=xproto.PropMode.Replace,
        window=x_window_id,
        property=WM_OPACITY_ATOM,
        type=xproto.Atom.CARDINAL,
        format=32,
        data_len=1,
        data=data)
    return void_cookie


# def set_opacity(x_window_id, opacity):
#     '''Set the opacity of a Xorg window'''
#     # If opacity already defined we need to unset it first
#     call(['xprop', '-id', str(x_window_id), '-remove',
#           '_NET_WM_WINDOW_OPACITY'])
#     call(['xprop', '-id', str(x_window_id), '-f', '_NET_WM_WINDOW_OPACITY',
#           '32c', '-set', '_NET_WM_WINDOW_OPACITY', str(opacity)])


# def delete_opacity_property(x_window_id):
#     '''Delete the _NET_WM_WINDOW_OPACITY property of a Xorg window'''
#     call(['xprop', '-id', str(x_window_id), '-remove',
#           '_NET_WM_WINDOW_OPACITY'])
