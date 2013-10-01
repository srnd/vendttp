######## CONFIGURATION FILE ########

#### Notes

# This is a default config file which should be copied as `settings.py` and
# edited for configuration purposes. When run, it will try to automatically
# copy itself as needed open itself in an editor.


#### Constants

NORMAL = 1
EMULATE = 2
SEARCH = None


#### Settings

# Each of the following corresponds to a device. Specify EMULATE, rather than
# NORMAL, to tell the server to expect an emulator (i.e.
# money_client_emulator.py, or rfid_scanner_emu.py,). Dispenser emulation is
# handled by server.py, and therefore doesn't require a separate script.

BILL_ACCEPTOR = NORMAL
RFID_SCANNER = NORMAL
DISPENSER = NORMAL

# Each of the following corresponds to a port to listen for a device on.
# You may either specify a port with a number or name, or choose to
# have the server search for the device. Note that searching is not
# guarunteed to properly identify devices, may cause unexpected behaviour,
# and for practical purposes should not be used in it's current state.

RFID_SCANNER_COMPORT = SEARCH #<- change this
DISPENSER_COMPORT = SEARCH #<- change this

# The following are used for testing with the emulated rfid scanner

#str
TESTING_RFID = "test"
#str
TESTING_USERNAME = "test.account"
#float
TESTING_BALANCE = 2.0


LOGFILE = "log.txt"

######## EXECUTABLE SCRIPT ########

if __name__ == "__main__":
    import os, sys, shutil
    if not os.path.exists('settings.py'):
        shutil.copy('settings_default.py', 'settings.py')
    if sys.platform.startswith('win'):
        os.system("notepad settings.py")
    elif sys.platform.startswith('linux'):
        os.system("gedit settings.py")
