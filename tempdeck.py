import argparse
import sys
from typing import List, Tuple

import serial
import serial.tools.list_ports


class _errors:
    class TempdeckControlError(Exception):
        pass

    class DeviceNotFound(TempdeckControlError):
        pass

    class InvalidResponse(TempdeckControlError):
        pass

    class ResponseTimeout(TempdeckControlError):
        pass


class TempdeckControl:
    TempdeckControlError = _errors.TempdeckControlError
    DeviceNotFound = _errors.DeviceNotFound
    InvalidResponse = _errors.InvalidResponse
    ResponseTimeout = _errors.ResponseTimeout

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


def parse_cli_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        epilog="If no action specified, read back current temperature values"
        )
    parser.add_argument(
        "-p", "--port",
        metavar="PORTNAME",
        help=(
            "Use serial port identified by PORTNAME "
            "(if not specified, connect to the first tempdeck found)"
            )
        )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "-l", "--list-devices",
        action='store_true',
        help="List port names for connected tempdecks"
        )
    action_group.add_argument(
        "-t", "--set-target",
        metavar="TEMP",
        type=float,
        help="Activate temperature control and set target to TEMP (in °C)"
        )
    action_group.add_argument(
        "-i", "--prompt-target",
        action='store_true',
        help="Prompt for target temperature and then set it"
        )
    action_group.add_argument(
        "-d", "--deactivate",
        action='store_true',
        help="Deactivate temperature control"
        )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_cli_args(sys.argv[1:])
    if args.list_devices:
        print("Found tempdecks on these ports:", file=sys.stderr)
        for portname in TempdeckControl.list_connected_devices():
            print(portname)
        sys.exit(0)
    if args.port:
        try:
            td = TempdeckControl.from_serial_portname(args.port)
        except serial.serialutil.SerialException as e:
            print(f"Couldn't open port {args.port!r}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            td = TempdeckControl.open_first_device()
        except TempdeckControl.DeviceNotFound:
            print("No tempdeck connected?", file=sys.stderr)
            sys.exit(1)
    target_temp = None
    deactivate = False
    if args.prompt_target:
        user_input = input(
            "Enter target temperature (\"off\" to deactivate): ")
        if user_input.strip().lower() == "off":
            deactivate = True
        else:
            target_temp = float(user_input)
    if target_temp is None:
        target_temp = args.set_target
    deactivate = args.deactivate or deactivate
    if target_temp is not None:
        td.set_target_temp(target_temp)
        new_target = td.get_target_temp()
        print(f"Target set to {new_target:.2f} °C")
    elif deactivate:
        td.deactivate()
        print("Temperature control deactivated")
    else:
        target_temp, current_temp = td.get_temps()
        print(
            "Target:  " + (
                f"{target_temp:.2f} °C"
                if target_temp is not None
                else "(deactivated)"
                )
            )
        print(f"Current: {current_temp:.2f} °C")
