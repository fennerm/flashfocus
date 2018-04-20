"""Testsuite for flashfocus.xutil."""
import sys

import xcffib

from flashfocus.xutil import focus_shifted
from test.helpers import change_focus


def test_focus_shifted(windows):
    del sys.modules['xpybutil']

    import xpybutil
    import xpybutil.window
    try:
        xpybutil.window.listen(xpybutil.root, 'PropertyChange')
    except xcffib.ConnectionException:
        pass
    change_focus(windows[1])
    assert focus_shifted()
