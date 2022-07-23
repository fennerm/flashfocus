class ConfigInitError(Exception):
    """Error when initializing the config file."""


class ConfigLoadError(Exception):
    """Error encountered while loading the config file."""


class WMError(Exception):
    """A window manager error."""


class UnexpectedMessageType(Exception):
    """I don't know what to do with this type of message."""


class UnsupportedWM(Exception):
    """I don't work with this window manager yet."""
