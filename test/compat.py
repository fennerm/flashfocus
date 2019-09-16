from flashfocus.compat import DisplayProtocol, get_display_protocol


if get_display_protocol() is DisplayProtocol.WAYLAND:
    # from flashfocus.display_protocols.sway import *
    pass
else:
    from test.x11_helpers import (  # noqa: F401
        change_focus as change_focus,
        clear_event_queue as clear_event_queue,
        create_blank_window as create_blank_window,
        set_fullscreen as set_fullscreen,
        switch_workspace as switch_workspace,
        unset_fullscreen as unset_fullscreen,
    )
