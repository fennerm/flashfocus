"""Manipulate Xorg window opacity."""
from __future__ import division

from select import select
from struct import pack

import xcffib
import xcffib.xproto as xproto

# Decimal representation of maximum opacity value accepted by X: 0xffffffff
MAX_OPACITY = 4294967295

class Cookie:
    """A response or event from the X server.

    Subclasses each implement their own unpack method for extracting the useful
    information from the response.
    """
    def __init__(self, cookie):
        self.cookie = cookie
        self.response = None


class OpacityCookie(Cookie):
    """A request for the current _NET_WM_WINDOW_OPACITY property of a window."""
    def unpack(self):
        """Parse the response from the X server.

        Returns
        -------
        float
            Opacity as a decimal. Returns None if _NET_WM_WINDOW_OPACITY is
            unset.

        """
        try:
            reply = self.cookie.reply().value.to_atoms()[0]
            self.response = int(reply) / MAX_OPACITY
        except IndexError:
            self.response = None
        return self.response


class ActiveWindowCookie(Cookie):
    """A request for the currently focused window."""
    def unpack(self):
        """Parse the response from the X server.

        Returns
        -------
        int
            The X window id of the active window

        """
        self.response = int(self.cookie.reply().focus)
        return self.response


class XConnection:
    def __init__(self, timeout=0):
        self.conn = xcffib.connect()
        self.timeout = timeout
        self.file_descriptor = self.conn.get_file_descriptor()
        # The id of the root X window
        self.root_window = self.conn.get_setup().roots[0].root
        # X ids for relevant window properties
        self.wm_opacity_atom = self.intern_atom('_NET_WM_WINDOW_OPACITY')
        self.active_window_atom = self.intern_atom('_NET_ACTIVE_WINDOW')

    def intern_atom(self, atom_name):
        """Get the id of an atom (property) from X given its name.

        Parameters
        ----------
        atom_name: str
            The name of an X atom, e.g '_NET_WM_WINDOW_OPACITY'.

        Returns
        -------
        int
            The X server's internal ID for the atom.

        """
        atom_bytes = atom_name.encode('ascii')
        cookie = self.conn.core.InternAtom(
            False, len(atom_bytes), atom_bytes)
        atom = cookie.reply().atom
        return atom

    def request_opacity(self, window):
        """Request the opacity of a window.

        Returns
        -------
        OpacityCookie

        """
        cookie = self.conn.core.GetProperty(
            delete=False,
            window=window,
            property=self.wm_opacity_atom,
            type=xproto.GetPropertyType.Any,
            long_offset=0,
            long_length=63
        )
        return OpacityCookie(cookie)

    def request_focus(self):
        """Request the currently focused window.

        Returns
        -------
        ActiveWindowCookie

        """
        cookie = self.conn.core.GetInputFocus()
        return ActiveWindowCookie(cookie)

    def set_opacity(self, window, opacity):
        """Set the _NET_WM_WINDOW_OPACITY property of a window.

        Blocks until the X session processes the request.

        Parameters
        ----------
        window: int
            The X id of a window
        opacity: float
            Opacity as a decimal < 1

        """
        data = pack('I', int(opacity * MAX_OPACITY))
        # Add argument names
        void_cookie = self.conn.core.ChangePropertyChecked(
            mode=xproto.PropMode.Replace,
            window=window,
            property=self.wm_opacity_atom,
            type=xproto.Atom.CARDINAL,
            format=32,
            data_len=1,
            data=data)
        void_cookie.check()

    def delete_opacity(self, window):
        """Delete the _NET_WM_WINDOW_OPACITY property from a window.

        Parameters
        ----------
        window: int
            The X id of a window

        """
        cookie = self.conn.core.GetProperty(
            delete=True,
            window=window,
            property=self.wm_opacity_atom,
            type=xproto.GetPropertyType.Any,
            long_offset=0,
            long_length=63
        )
        cookie.reply()

    def start_watching_properties(self, window):
        """Start monitoring property changes for a window."""
        # To handle events in xcb we need to add a 'mask' to the window, which
        # informs the X server that we should notified when the masked event
        # occurs.
        property_mask = getattr(xproto.EventMask, 'PropertyChange')

        # We also check for KeyPress events so that the program shuts down
        # immediately when Ctrl-C is pressed.
        keyboard_mask = getattr(xproto.EventMask, 'KeyPress')
        mask = property_mask | keyboard_mask
        self.conn.core.ChangeWindowAttributesChecked(
            window,
            xproto.CW.EventMask,
            [mask]).check()

    def has_events(self):
        """True if the X connection has events which have not been processed."""
        return select([self.file_descriptor], [], [], self.timeout)[0]

    def focus_shifted(self):
        """Return True if the last subscribed X event was a focus shift."""
        event = self.conn.poll_for_event()

        if event:
            if isinstance(event, xproto.PropertyNotifyEvent):
                if event.atom == self.active_window_atom:
                    return True
        return False
