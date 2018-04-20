"""Manipulate Xorg window opacity."""
import xcffib
import xcffib.xproto
import xpybutil
import xpybutil.window


def focus_shifted():
    """Return True if focus shifted since last poll."""
    event = xpybutil.conn.wait_for_event()
    if isinstance(event, xcffib.xproto.PropertyNotifyEvent):
        return xpybutil.util.get_atom_name(event.atom) == '_NET_ACTIVE_WINDOW'
    else:
        return False
