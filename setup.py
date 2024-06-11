from setuptools import setup


setup(
    name="ot_tempdeck",
    version="0.1.1",
    packages=["ot_tempdeck"],
    install_requires=["pyserial"],  # TODO figure out min version
    entry_points={
        'console_scripts': [
            'tempdeck-ctrl = ot_tempdeck.cli:_cli_entry_point']
        }
    )
