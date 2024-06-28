# BLV-Uplink-Downlink

## Overview
CubeSatLink is a software project to establish a reliable communication link between a ground station and several student-built CubeSats (small satellites) attached to a flying weather balloon mission. The project aims to provide a robust and efficient communication system for CubeSat missions with minimal effort on the student's side, enabling quick prototyping of the yearlong Balloon Launch Assessment Directive for Everyone (BLADE) launched in Summer-Fall.

## Features
**Reliable Data Transfer**: CubeSatLink ensures reliable data transfer between the CubeSat and the ground station, even in errors or packet loss.
**Flexible Configuration**: The project allows for flexible configuration of communication parameters, such as data rates, packet sizes, data bits, stop bits, and parity controls.
**Ground Station Software**: The project includes a comprehensive ground station software suite for monitoring received packets, and sending instructions to CubeSats through console terminal.
**SDCard Memory Support**: The ground station supports data storage on an SDCard for permanent storage of sent and received data in case of ground station malfunction.

## Technical Details
**Programming Languages**: The project is written in C++ and Python.
**Communication Protocols**: The system utilizes UART and SPI communication protocols. It is designed to accommodate UTF-8 encoded string for both communication directions.
**Hardware Requirements**: The project is designed to work with various CubeSat hardware platforms given the variety of student hardware and the number of CubeSats launched.

## Contributing
Contributions to BLV_CubeSatLink are welcome! If you'd like to contribute, please fork the repository, make your changes, and submit a pull request.

## License
BLV_CubeSatLink is licensed under the MIT License.

## Acknowledgments
The BLV_CubeSatLink project is developed and maintained by SP1RYTUSzz for Cal Poly Pomona's BroncoSpace. We acknowledge the contributions of all developers, testers, and users who have helped shape this project. :")

## Contact
For questions, issues, or feedback, please open an issue on GitHub or contact the project maintainer at trisdo37@gmail.com.
