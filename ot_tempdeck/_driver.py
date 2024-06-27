from typing import Any, Callable, Dict, List, Optional, Tuple


import serial
import serial.tools.list_ports

from .types import *


class TempdeckControl:
    """Driver for communicating with an Opentrons Tempdeck"""

    TempdeckControlError = TempdeckControlError
    DeviceNotFound = DeviceNotFound
    InvalidResponse = InvalidResponse
    ResponseTimeout = ResponseTimeout

    USB_VID = 0x04d8
    USB_PID = 0xee93

    def __init__(self, ser_port: serial.Serial):
        """
        :param ser_port: a ``serial.Serial`` instance (or other object with a
            compatible interface) that will be used to communicate with the
            Tempdeck
        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        self.ser_port = ser_port
        self._populate_device_info()

    @classmethod
    def open_first_device(cls, *args, **kwargs) -> 'TempdeckControl':
        """
        Look for any connected Tempdecks (see :meth:`list_connected_devices`)
        and open the first one found.

        :raises DeviceNotFound: If no tempdecks were found
        :raises serial.SerialException: If something went wrong opening the
            serial device
        """
        portnames = cls.list_connected_devices()
        if not portnames:
            raise cls.DeviceNotFound("No tempdeck detected")
        return cls.from_serial_portname(portnames[0])

    @classmethod
    def from_serial_portname(cls, portname: str, *args, **kwargs
                             ) -> 'TempdeckControl':
        """
        Open the specified serial port and initialize a new
        :class:`TempdeckControl`.

        :param portname: Port name or URL to pass to ``serial.Serial()``

        :returns: New :class:`TempdeckControl` instance

        :raises serial.SerialException: If something went wrong opening the
            serial device
        """
        ser_port = serial.Serial(portname, timeout=0.5, xonxoff=True)
        return cls(ser_port, *args, **kwargs)

    @classmethod
    def list_connected_devices(cls) -> List[str]:
        """
        Get a list of serial port names corresponding to Opentrons Tempdecks.
        Checks for virtual serial ports corresponding to USB devices with the
        appropriate VID/PID.

        Only supported on Windows, macOS and Linux.

        :returns: A list of serial port device names
            (naming convention is platform-dependent)
        """
        return [
            info.device
            for info in serial.tools.list_ports.comports()
            if info.vid == cls.USB_VID and info.pid == cls.USB_PID
            ]

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

    def _ask(self, cmd: str, types: Optional[Dict[str, Callable]] = None
             ) -> Tuple[Dict[str, Any], str]:
        self._send_command(cmd)
        types = dict(types or ())
        response = self._read_line().strip()
        self._wait_for_ack()
        info = {}
        for piece in response.split():
            try:
                left, right = piece.split(":", 1)
                info[left] = types.get(left, str)(right)
            except ValueError as e:
                raise self.InvalidResponse(
                    f"Couldn't parse this part: {piece!r} -- "
                    f"full response was {response!r}"
                    ) from e
        return info, response

    def _populate_device_info(self) -> Dict[str, str]:
        info, response = self._ask("M115")
        for key in ['model', 'serial', 'version']:
            if key not in info:
                raise self.InvalidResponse(
                    f"Response missing value for {key}: {response!r}")
        self._model_name = info['model']
        self._serial_no = info['serial']
        self._fw_version = info['version']

    def set_target_temp(self, temp: float):
        """
        Set the Tempdeck's target temperature to the supplied value and
        activate it if it wasn't active.

        :param temp: Target temperature in °C

        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        self._send_command(f"M104 S{temp:.3f}")
        self._wait_for_ack()

    def get_temps(self) -> Tuple[Optional[float], float]:
        """
        Get the current temperature setpoint and measured temperature from the
        Tempdeck.

        :returns: A tuple ``(target_temp, current_temp)`` containing the
            current setpoint and measured temperature, respectively, in °C.
            ``target_temp`` will be ``None`` if the tempdeck is currently
            deactivated.

        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        float_or_none = lambda x: None if x == "none" else float(x)
        info, response = self._ask(
            "M105", types={'C': float, 'T': float_or_none})
        for key, desc in [('C', "current temp"), ('T', "target temp")]:
            if key not in info:
                raise self.InvalidResponse(
                    f"Response missing value for {desc}: {response!r}")
        return info['T'], info['C']  # (target temp, current temp)

    def get_target_temp(self) -> Optional[float]:
        """
        Read the current temperature setpoint from the Tempdeck.

        Note: If you need both the target temperature and the current measured
        temperature it is more efficient to call :meth:`get_temps`.

        :returns: The current temperature setpoint in °C, or ``None`` if the
            tempdeck is currently deactivated

        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        target_temp, current_temp = self.get_temps()
        return target_temp

    def get_current_temp(self) -> float:
        """
        Read the current measured temperature from the Tempdeck.

        Note: If you need both the target temperature and the current measured
        temperature it is more efficient to call :meth:`get_temps`.

        :returns: The current measured temperature in °C

        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        target_temp, current_temp = self.get_temps()
        return current_temp

    def deactivate(self):
        """
        Clear the temperature setpoint and deactivate heating and cooling.

        :raises ResponseTimeout, InvalidResponse: see class descriptions
        """
        self._send_command("M18")

    @property
    def model_name(self) -> str:
        """Model name reported by the Tempdeck"""
        return self._model_name

    @property
    def serial_no(self) -> str:
        """Serial number reported by the Tempdeck"""
        return self._serial_no

    @property
    def fw_version(self) -> str:
        """Firmware version reported by the Tempdeck"""
        return self._fw_version
