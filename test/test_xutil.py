"""Testsuite for flashfocus.xutil."""
import xcffib
import xpybutil
import xpybutil.window

from flashfocus.xutil import focus_shifted
from test.helpers import change_focus


def test_focus_shifted(fresh_xpybutil, windows):
    try:
        xpybutil.window.listen(xpybutil.root, 'PropertyChange')
    except xcffib.ConnectionException:
        pass
    change_focus(windows[1])
    assert focus_shifted()
