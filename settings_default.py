########## !IMPORTANT! ##########
# This is a default config file #
#    which will be copied to    #
# settings.py on the first run  #
#         of server.py.         #
#################################

###############
OFF = 0       #
ON = 1        #
EMULATE = 2   #
SEARCH = None #
###############

# Each of the following corresponds to a device.
# Turn them on or off, or force emulator compatability for debugging.

BILL_ACCEPTOR = ON
RFID_SCANNER = ON
DISPENSER = ON

# Each of the following corresponds to a port to listen for a device on.
# You may either specify a port with a number or string (preferred), or choose
# to have the server search for the device. Note that searching is not garunteed
# to successfully identify devices.

RFID_SCANNER_COMPORT = SEARCH
DISPENSER_COMPORT = SEARCH
