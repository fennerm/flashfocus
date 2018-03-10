'''Manipulate Xorg window opacity'''

from subprocess import (
    call,
    check_output,
)


def get_window_opacity(x_window_id):
    '''Get the opacity of a window from its Xorg window id'''
    opacity = check_output(
        'xprop -id ' + str(x_window_id) +
        ' | grep _NET_WM_WINDOW_OPACITY | sed -ne "s/^.*= //p"', shell=True)
    opacity = opacity.decode('utf-8').strip()
    return opacity


def get_window_opacity_atom(xcb_connection):
    atom_bytes = '_NET_WM_WINDOW_OPACITY'.encode('ascii')
    wm_opacity_atom_cookie = xcb_connection.core.InternAtom(
        only_if_exists=False,
        name_length=len(atom_bytes),
        name=atom_bytes)
    wm_opacity_atom = wm_opacity_atom_cookie.reply().atom
    return wm_opacity_atom


def get_window_opacity2(x_window_id):
    import xcffib as xcb
    import xcffib.xproto
    xcb_connection = xcb.connect()
    wm_opacity_atom = get_window_opacity_atom(xcb_connection)
    wm_opacity_cookie = xcb_connection.core.GetProperty(
        delete=False,
        window=x_window_id,
        atom=wm_opacity_atom,
        type=xproto.GetPropertyType.Any,
        long_offset=0,
        long_length=63)


def set_opacity(x_window_id, opacity):
    '''Set the opacity of a Xorg window'''
    # If opacity already defined we need to unset it first
    call(['xprop', '-id', str(x_window_id), '-remove',
          '_NET_WM_WINDOW_OPACITY'])
    call(['xprop', '-id', str(x_window_id), '-f', '_NET_WM_WINDOW_OPACITY',
          '32c', '-set', '_NET_WM_WINDOW_OPACITY', str(opacity)])


def delete_opacity_property(x_window_id):
    '''Delete the _NET_WM_WINDOW_OPACITY property of a Xorg window'''
    call(['xprop', '-id', str(x_window_id), '-remove',
          '_NET_WM_WINDOW_OPACITY'])
