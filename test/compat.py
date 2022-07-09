from flashfocus.compat import DisplayProtocol, get_display_protocol

if get_display_protocol() is DisplayProtocol.WAYLAND:
    # from flashfocus.display_protocols.sway import *
    pass
else:
    from test.x11_helpers import change_focus as change_focus  # noqa: F401
    from test.x11_helpers import clear_event_queue as clear_event_queue
    from test.x11_helpers import create_blank_window as create_blank_window
    from test.x11_helpers import set_fullscreen as set_fullscreen
    from test.x11_helpers import switch_workspace as switch_workspace
    from test.x11_helpers import unset_fullscreen as unset_fullscreen
