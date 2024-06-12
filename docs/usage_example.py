from ot_tempdeck import TempdeckControl


# List the serial port names corresponding to detected tempdecks:
portnames = TempdeckControl.list_connected_devices()
# -> ["/dev/ttyACM0"]

# Open the first/only detected device
td = TempdeckControl.open_first_device()
# ...or explicitly specify a port name, e.g.:
# td = TempdeckControl.from_serial_portname("/dev/ttyACM0")

# Get the current setpoint and measured temperature:
target_temp, current_temp = td.get_temps()
# -> (None, 25.621)

# Alternatively,
current_temp = td.get_current_temp()
# -> 25.619
target_temp = td.get_target_temp()
# -> None

# Activate the tempdeck and set target to 35degC
td.set_target_temp(35.0)

target_temp, current_temp = td.get_temps()
# -> (35.0, 25.927)

# Deactivate heating/cooling again
td.deactivate()
