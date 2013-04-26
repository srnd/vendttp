########## !IMPORTANT! ##########
# This is a default config file #
#    which will be copied to    #
# settings.py on the first run  #
#  of server.py. Edit it if you #
#   want non-default settings   #
#################################

#############
OFF = 0
ON = 1
SEARCH = None
EMULATE = 2
#############

# Each of the following corresponds to a device.
# For testing purposes, you may turn off the listener for a device.

BILL_ACCEPTOR = ON
RFID_SCANNER = ON
DISPENSER = ON

# Each of the following corresponds to a port to listen for a device on.
# You may either specify a port with a number or string, or choose to have the
# server search for the device.

RFID_SCANNER_COMPORT = SEARCH
DISPENSER_COMPORT = SEARCH
