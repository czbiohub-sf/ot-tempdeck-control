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

    USB_HW_IDS = [
        (0x04d8, 0xee93),
        ]

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
    def open_first_device(
            cls,
            usb_vidpid: Optional[Tuple[int, int]] = None,
            **kwargs) -> 'TempdeckControl':
        """
        Look for any connected Tempdecks (see :meth:`list_connected_devices`)
        and open the first one found.

        :param usb_vidpid: A tuple ``(vid, pid)`` specifying a particular
            USB vendor and product ID to look for instead of using the standard
            values.
        :param kwargs: keyword arguments to pass to :meth:`__init__`
        :raises DeviceNotFound: If no tempdecks were found
        :raises serial.SerialException: If something went wrong opening the
            serial device
        """
        dev_list = cls.list_connected_devices(usb_vidpid=usb_vidpid)
        if not dev_list:
            raise cls.DeviceNotFound("No Tempdecks found")
        return cls.from_serial_portname(dev_list[0][0], **kwargs)

    @classmethod
    def from_usb_location(
            cls,
            location: str,
            usb_vidpid: Optional[Tuple[int, int]] = None,
            **kwargs) -> 'TempdeckControl':
        """
        Connects to a Tempdeck at a specific USB port.

        :param location: A string representing the USB port location, as
            obtained from :meth:`list_connected_devices`
        :param usb_vidpid: A tuple ``(vid, pid)`` specifying a particular
            USB vendor and product ID to look for instead of using the standard
            values
        :param kwargs: keyword arguments to pass to :meth:`__init__`
        :raises DeviceNotFound: If no Tempdeck was detected with a matching USB
            location string
        :raises serial.SerialException: If something went wrong opening the
            serial device

        (also see exceptions raised by :meth:`__init__`)
        """
        for portname, location_ in cls.list_connected_devices(
                usb_vidpid=usb_vidpid):
            if location_ == location:
                return cls.from_serial_portname(portname, **kwargs)
        raise cls.DeviceNotFound(
            f"No Tempdeck detected at USB location {location!r}")

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
    def list_connected_devices(
            cls, usb_vidpid: Optional[Tuple[int, int]] = None
            ) -> List[Tuple[str, str]]:
        """
        Get a list of all Tempdecks currently connected via USB. Detection is
        based on the USB vendor/product ID values reported by the OS. This
        method does not attempt to open the devices or verify that they are
        actually accessible.

        Only supported on Windows, macOS and Linux.

        :param usb_vidpid: A tuple ``(vid, pid)`` specifying a particular
            USB vendor and product ID to look for instead of the standard
            values.
        :returns: A list of tuples ``(portname, location)`` where ``portname``
            the name of a logical serial port (e.g. ``"COM42"`` or
            ``"/dev/ttyACM0"``) as recognized by pySerial and ``location`` is
            a string representing which actual USB port the Tempdeck is
            connected to. The latter is useful for connecting to a specific
            Tempdeck (see :meth:`from_usb_location`) since they don't expose a
            serial number via USB descriptors.
        """
        usb_vidpids = (
            [tuple(usb_vidpid)] if usb_vidpid is not None
            else cls.USB_HW_IDS
            )
        return [
            (info.device, info.location)
            for info in serial.tools.list_ports.comports()
            if (info.vid, info.pid) in usb_vidpids
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
