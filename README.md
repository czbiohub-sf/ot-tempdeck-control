# ot-tempdeck-control
This is a lightweight Python driver and command-line tool for controlling the Opentrons Temperature Module ("Tempdeck").

This project is not affiliated with Opentrons.

## Key directory contents
- `ot_tempdeck/` - Python package
- `docs/` - Sphinx documentation project
- `tempdeck-ctrl.py` - Wrapper script to run the CLI in-place without installing `ot-tempdeck-control`

## Requirements
The `ot_tempdeck` package requires:
- Python >= 3.6
- `pyserial` >= 3.5 (earlier versions may work, not tested).

Building the docs requires `sphinx`.

## Installation
Activate a virtual environment if desired, then, from the root of this distribution, run:
```
pip install .
```

To build the documentation:
```
cd docs
make html
```
Open `docs/html/_build/index.html` in a web browser to view the API documentation.
Other formats are available as well; run `make` with no arguments for a list.

## API usage
Refer to the docstrings or compiled documentation for full API usage information with examples. The examples from the documentation can also be found in `docs/usage_example.py`.

## Command line tool
This package provides the `tempdeck-ctrl` command. Usage is shown below.
```
$ tempdeck-ctrl -h
usage: tempdeck-ctrl [-h] [-p PORTNAME] [-l | -t TEMP | -i | -d]

optional arguments:
  -h, --help            show this help message and exit
  -p PORTNAME, --port PORTNAME
                        Use serial port identified by PORTNAME (if not specified, connect to the first tempdeck found)
  -l, --list-devices    List port names for connected tempdecks
  -t TEMP, --set-target TEMP
                        Activate temperature control and set target to TEMP (in °C)
  -i, --prompt-target   Prompt for target temperature and then set it
  -d, --deactivate      Deactivate temperature control

If no action specified, read back current temperature values
```

For further information and examples, see the documentation.

To use the command line tool without installing the package, you can run `python tempdeck-ctrl.py` from the root of this distribution.

## Support
This repository is maintained by Greg Courville of the Bioengineering Platform of Chan Zuckerberg Biohub San Francisco.
