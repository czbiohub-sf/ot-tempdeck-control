class TempdeckControlError(Exception):
    """Base class for TempdeckControl errors."""
    pass


class DeviceNotFound(TempdeckControlError):
    """Indicates that no tempdecks were detected."""
    pass


class InvalidResponse(TempdeckControlError):
    """
    Raised when the response received to a command doesn't match the expected
    format.
    """
    pass


class ResponseTimeout(TempdeckControlError):
    """
    Raised if the remote device doesn't send back a line of text within a
    prescribed period of time.

    One common situatuation that can cause this is accidentally connecting
    to a serial device that's not a Tempdeck.
    """
    pass
