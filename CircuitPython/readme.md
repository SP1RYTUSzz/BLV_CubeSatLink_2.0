BLV CubeSatLink CircuitPython
=====================================

**Description**

This folder contains python script files and associated .mpy library for the two Feathers used in the project.

**Contents**

This repository contains the following files and directories:
Summit.py: Flight Transceiver main code. To be renamed into "code.py" before copied to the Feather boards.
GroundStation.py: Ground Station main code. To be renamed into "code.py" before copied to the Feather boards.
adafruit_datetime.mpy, adafruit_rfm9x.mpy: to be copied into both Feather boards.

**Requirements**

Feather RP2040 *2
Raspberry Pi Pico *1
Connection between Pico and Feather (TBA)

**Setup**

Plug battery into Summit first, make sure red LED is flashing (transmitting data).

**Usage**

Connect Ground Station to computer using a USB cable.
Open a serial terminal program (e.g. PuTTY or screen) and connect to the Feather board's serial port.
Press the reset button on the Feather board to start the program.
The program will print output to the serial terminal.

Authors
SP1RYTUSzz
Version History
2024-08-02: Initial commit
