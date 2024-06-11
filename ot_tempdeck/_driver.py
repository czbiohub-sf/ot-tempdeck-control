from typing import List, Tuple

import serial
import serial.tools.list_ports

from .types import *


__all__ = ["TempdeckControl"]


class TempdeckControl:
    TempdeckControlError = TempdeckControlError
    DeviceNotFound = DeviceNotFound
    InvalidResponse = InvalidResponse
    ResponseTimeout = ResponseTimeout

    USB_VID = 0x04d8
    USB_PID = 0xee93

    def __init__(self, ser_port: serial.Serial):
        self.ser_port = ser_port

    @classmethod
    def list_connected_devices(cls) -> List[str]:
        return [
            info.device
            for info in serial.tools.list_ports.comports()
            if info.vid == cls.USB_VID and info.pid == cls.USB_PID
            ]

    @classmethod
    def open_first_device(cls, *args, **kwargs) -> 'TempdeckControl':
        portnames = cls.list_connected_devices()
        if not portnames:
            raise cls.DeviceNotFound("No tempdeck detected")
        return cls.from_serial_portname(portnames[0])

    @classmethod
    def from_serial_portname(cls, portname: str, *args, **kwargs
                             ) -> 'TempdeckControl':
        ser_port = serial.Serial(portname, timeout=0.5, xonxoff=True)
        return cls(ser_port, *args, **kwargs)

    def _send_command(self, cmd: str):
        self.ser_port.write(f"{cmd}\r\n".encode('ascii'))

    def _read_line(self) -> str:
        line = self.ser_port.readline().decode('ascii')
        if (not line) or  line[-1] != "\n":
            raise self.ResponseTimeout()
        return line.rstrip()

    def _wait_for_ack(self):
        for i in range(2):
            line = self._read_line()
            if line != "ok":
                raise self.InvalidResponse(
                    f"Unexpected response when we expected 'ok': {line!r}")

    def set_target_temp(self, temp: float):
        self._send_command(f"M104 S{temp:.3f}")
        self._wait_for_ack()

    def get_temps(self) -> Tuple[float, float]:
        self._send_command(f"M105")
        response = self._read_line().strip()
        target_temp = None
        current_temp = None
        tokens = response.split()
        try:
            for token in tokens:
                left, right = token.split(":", 1)
                if left == "C":
                    current_temp = float(right)
                elif left == "T":
                    target_temp = float(right) if right != "none" else right
        except ValueError as e:
            raise self.InvalidResponse(
                f"Error parsing response: {response!r}"
                ) from e
        for var_name in ['target_temp', 'current_temp']:
            if locals()[var_name] is None:
                raise self.InvalidResponse(
                    f"Response missing value for {var_name.replace('_', ' ')}:"
                    + repr(response)
                    )
        self._wait_for_ack()
        return (target_temp if target_temp != "none" else None, current_temp)

    def get_target_temp(self) -> float:
        target_temp, current_temp = self.get_temps()
        return target_temp

    def get_current_temp(self) -> float:
        target_temp, current_temp = self.get_temps()
        return current_temp

    def deactivate(self):
        self._send_command("M18")
