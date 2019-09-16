import subprocess
from time import sleep

import xcffib
import xcffib.xproto
import xpybutil
import xpybutil.ewmh
from xpybutil.ewmh import request_wm_state_checked, set_active_window_checked
from xpybutil.util import get_atom


from flashfocus.compat import Window


def change_focus(window):
    """Change the active window."""
    set_active_window_checked(window.id).check()
    sleep(0.01)


def clear_event_queue() -> None:
    while xpybutil.conn.poll_for_event():
        pass


def create_blank_window(wm_name=None, wm_class=None):
    """Create a blank Xorg window."""
    setup = xpybutil.conn.get_setup()
    window = Window(xpybutil.conn.generate_id())
    xpybutil.conn.core.CreateWindow(
        setup.roots[0].root_depth,
        window.id,
        setup.roots[0].root,
        0,
        0,
        640,
        480,
        0,
        xcffib.xproto.WindowClass.InputOutput,
        setup.roots[0].root_visual,
        xcffib.xproto.CW.BackPixel | xcffib.xproto.CW.EventMask,
        [
            setup.roots[0].white_pixel,
            xcffib.xproto.EventMask.Exposure | xcffib.xproto.EventMask.KeyPress,
        ],
    )
    xpybutil.conn.core.MapWindow(window.id)
    xpybutil.conn.flush()
    if wm_class:
        window.set_class(wm_class[0], wm_class[1])
    if wm_name:
        window.set_name(wm_name)
    return window


def switch_workspace(workspace: int) -> None:
    # unfortunately need to use i3 specific command here because i3 blocks
    # external desktop switch requests
    subprocess.check_output(["i3-msg", "workspace", str(workspace)])


def set_fullscreen(window: Window) -> None:
    request_wm_state_checked(
        window.id, action=1, first=get_atom("_NET_WM_STATE_FULLSCREEN")
    ).check()


def unset_fullscreen(window: Window) -> None:
    request_wm_state_checked(
        window.id, action=0, first=get_atom("_NET_WM_STATE_FULLSCREEN")
    ).check()
