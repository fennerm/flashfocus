class ConfigInitError(Exception):
    """Error when initializing the config file."""

    pass


class ConfigLoadError(Exception):
    """Error encountered while loading the config file."""

    pass


class WMError(Exception):
    """A window manager error."""

    pass


class UnexpectedMessageType(Exception):
    """I don't know what to do with this type of message."""

    pass


class UnsupportedWM(Exception):
    """I don't work with this window manager yet."""

    pass
