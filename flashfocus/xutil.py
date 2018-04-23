"""Manipulate Xorg window opacity."""
from xcffib.xproto import PropertyNotifyEvent
import xpybutil
import xpybutil.window


def focus_shifted():
    """Return True if focus shifted since last poll."""
    event = xpybutil.conn.wait_for_event()
    if isinstance(event, PropertyNotifyEvent):
        return xpybutil.util.get_atom_name(event.atom) == '_NET_ACTIVE_WINDOW'
        return False
