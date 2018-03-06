'''Manipulate Xorg window opacity'''


def get_window_opacity(x_window_id):
    '''Get the opacity of a window from its Xorg window id'''
    opacity = check_output(
        'xprop -id ' + str(x_window_id) +
        ' | grep _NET_WM_WINDOW_OPACITY | sed -ne "s/^.*= //p"', shell=True)
    opacity = opacity.decode('utf-8').strip()
    return opacity


def set_opacity(x_window_id, opacity):
    '''Set the opacity of a Xorg window'''
    # If opacity already defined we need to unset it first
    call(['xprop', '-id', str(x_window_id), '-remove',
          '_NET_WM_WINDOW_OPACITY'])
    call(['xprop', '-id', str(x_window_id), '-f', '_NET_WM_WINDOW_OPACITY',
          '32c', '-set', '_NET_WM_WINDOW_OPACITY', str(opacity)])


def delete_opacity_property(x_window_id):
    '''Delete the _NET_WM_WINDOW_OPACITY property of a Xorg window'''
    call(['xprop', '-id', str(x_window_id), '-remove', '_NET_WM_WINDOW_OPACITY'])
