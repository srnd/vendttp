# VendTTP
Software to run StudentRND's Frankensteinian vending machine.

## To use:
1.  (optional) Start arduino IDE to discover which port the arduino is connected on.
2.  create or edit the settings.py to specify the arduino and RFID scanner ports.
3.  Start server.py.
4.  Start the windows phone client.
5.  Point the windows phone client to the server IP.

## Requirements:
* Python 2.x
* [PySerial](http://pyserial.sourceforge.net/) if you plan on using this with the real vending machine and RFID scanner; not necessary for emulated controllers and scanner.
