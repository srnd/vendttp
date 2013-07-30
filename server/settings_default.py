########## !IMPORTANT! ##########
# This is a default config file #
#   which should be copied as   #
#    settings.py and edited.    #
#################################

#######################
NORMAL = 1            #
EMULATE = 2           #
SEARCH = None         #
#######################

# Each of the following corresponds to a device. Specify EMULATE to tell the
# server to expect an emulator (i.e. money_client_emulator.py, or
# rfid_scanner_emu.py,). Dispenser emulation is handled by server.py, and
# therefore doesn't require a separate script.

BILL_ACCEPTOR = NORMAL
RFID_SCANNER = NORMAL
DISPENSER = NORMAL

# Each of the following corresponds to a port to listen for a device on.
# You may either specify a port with a number or name, or choose to
# have the server search for the device. Note that searching is not
# guarunteed to properly identify devices.

RFID_SCANNER_COMPORT = SEARCH
DISPENSER_COMPORT = SEARCH
