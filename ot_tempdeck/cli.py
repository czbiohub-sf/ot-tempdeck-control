import argparse
import sys
from typing import List

import serial

from . import TempdeckControl


def parse_cli_args(argv_rh: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        epilog="If no action specified, read back current temperature values"
        )
    devselect_group = parser.add_mutually_exclusive_group()
    devselect_group.add_argument(
        "-p", "--port",
        metavar="PORTNAME",
        help="Use serial port identified by PORTNAME"
        )
    devselect_group.add_argument(
        "-u", "--usb",
        metavar="LOCATION",
        help="Select device according to USB port location string"
        )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "-l", "--list-devices",
        action='store_true',
        help="List detected tempdecks"
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
    return parser.parse_args(argv_rh)


def cli_main(argv_rh: List[str]) -> int:
    args = parse_cli_args(argv_rh)
    if args.list_devices:
        print(
            "Found tempdecks on these ports (serial port name, USB location):",
            file=sys.stderr
            )
        for portname, location in TempdeckControl.list_connected_devices():
            print(f"{portname}, {location}")
        return 0
    try:
        if args.port:
            td = TempdeckControl.from_serial_portname(args.port)
        elif args.usb:
            td = TempdeckControl.from_usb_location(args.usb)
        else:
            td = TempdeckControl.open_first_device()
    except TempdeckControl.DeviceNotFound as e:
        print(str(e), file=sys.stderr)
        return 1
    except serial.serialutil.SerialException as e:
        print(f"Couldn't open port {args.port!r}: {e}", file=sys.stderr)
        return 1
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
    return 0


def _cli_entry_point():
    sys.exit(cli_main(sys.argv[1:]))


if __name__ == "__main__":
    _cli_entry_point()
