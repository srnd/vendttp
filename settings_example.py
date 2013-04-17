########## !IMPORTANT! ##########
# save this file as settings.py #
#################################

#############
OFF = 0
ON = 1
SEARCH = None
#############

# Each of the following corresponds to a device.
# For testing purposes, you may turn off the listenerer for a device.

BILL_ACCEPTOR = ON
RFID_SCANNER = ON
DISPENSER = ON

# Each of the following corresponds to a port to listen for a device on.
# You may either specify a port with a number or string, or choose to have the
# server search for the device.

RFID_SCANNER_COMPORT = SEARCH
DISPENSER_COMPORT = SEARCH
