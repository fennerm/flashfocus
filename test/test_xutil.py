"""Testsuite for flashfocus.xutil."""
import xcffib
import xpybutil

from flashfocus.xutil import focus_shifted
from test.helpers import change_focus


def test_focus_shifted(windows):
    xpybutil.conn = xcffib.connect()
    xpybutil.window.listen(xpybutil.root, 'PropertyChange')
    change_focus(windows[1])
    assert focus_shifted()
