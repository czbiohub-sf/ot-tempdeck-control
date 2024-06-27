``ot_tempdeck`` module
=========================

Driver class
------------
.. autoclass:: ot_tempdeck.TempdeckControl
   :members: __init__, list_connected_devices, open_first_device, from_serial_portname, from_usb_location, set_target_temp, get_temps, get_target_temp, get_current_temp, deactivate, model_name, serial_no, fw_version
   :member-order: bysource

Exceptions
----------
.. autoclass:: ot_tempdeck.TempdeckControl.TempdeckControlError
.. autoclass:: ot_tempdeck.TempdeckControl.DeviceNotFound
   :show-inheritance: True
.. autoclass:: ot_tempdeck.TempdeckControl.InvalidResponse
   :show-inheritance: True
.. autoclass:: ot_tempdeck.TempdeckControl.ResponseTimeout
   :show-inheritance: True

Usage example
-------------
.. literalinclude:: usage_example.py
   :language: python

Command line tool
=================
A command-line tool :program:`tempdeck-ctrl` is also included.

Usage
-----
The package installs a command called ``tempdeck-ctrl`` whose usage is described below.

``tempdeck-ctrl [-p PORTNAME] [-h | -l | -t TEMP | -d | -i]``

A script file ``tempdeck-ctrl.py`` is also provided in the top-level directory of the source distribution to allow running the tool in-place without installing the package. Its usage mirrors the ``tempdeck-ctrl`` command. ::

   $ cd /path/to/ot-tempdeck-control
   $ python tempdeck-ctrl.py [...]

.. program:: tempdeck-ctrl

Actions
^^^^^^^
The default action if none of the following flags are given is to read back and print the current measured and target temperatures along with information about the device. The following additional actions are available:

.. option:: -h, --help

   Print usage information and exit.

.. option:: -l, --list-devices

   Print a list of serial ports and corresponding USB port locations on which Tempdecks were detected (see :py:meth:`ot_tempdeck.TempdeckControl.list_connected_devices()`).

.. option:: -t TEMP, --set-target TEMP

   Set temperature setpoint to TEMP (in °C).

.. option:: -d

   Clear setpoint and deactivate temperature control.

.. option:: -i

   "Interactive mode" -- prompt for a new target temperature (or the word "off") and then set the target temperature or deactivate the tempdeck accordingly and exit.

Configuration options
^^^^^^^^^^^^^^^^^^^^^

.. option:: -p PORTNAME, --port PORTNAME

   Specify the serial port to connect to. If a port is not specified, the first detected tempdeck will be used.

.. option:: -u LOCATION, --usb LOCATION

   Use the tempdeck connected to the USB port at LOCATION

Examples
--------
Show devices currently connected: ::

   $ tempdeck-ctrl -l
   Found tempdecks on these ports (serial port name, USB location):
   COM5, 1-3.3
   COM9, 1-4:x.0

Get current temperature values: ::

   $ tempdeck-ctrl -p COM9
   Port:      COM9
   Model:     temp_deck_v4.0
   Serial no: TDV04P20770101B04
   Target:    (deactivated)
   Current:   22.56 °C

If only one tempdeck is connected, you can omit the :option:`-p` and :option:`-u` options, as in the remaining examples below.

Activate tempdeck and set target to 42.3°C: ::

   $ tempdeck-ctrl -t 42.3
   Target set to 42.30 °C

Check temperature values while tempdeck is heating up: ::

   $ tempdeck-ctrl
   Port:      COM9
   Model:     temp_deck_v4.0
   Serial no: TDV04P20770101B04
   Target:  42.30 °C
   Current: 32.18 °C

Deactivate tempdeck again: ::

   $ tempdeck-ctrl -d
   Temperature control deactivated
