class TempdeckControlError(Exception):
    pass


class DeviceNotFound(TempdeckControlError):
    pass


class InvalidResponse(TempdeckControlError):
    pass


class ResponseTimeout(TempdeckControlError):
    pass
