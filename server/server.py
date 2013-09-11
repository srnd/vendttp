#!/usr/bin/env python2.7
if __name__ == '__main__': print "Loading..."

######## IMPORTS ########

# system imports
import atexit, codecs, json, os, socket, subprocess, sys, threading, time
# local imports
import database
from AccountManager import AccountManager
from util import settings, credentials, \
                 SoldOut, BadItem, InsufficientFunds, \
                 URLOpenError, JSONDecodeError

######## SETUP ########

try:
  from ThreadSafeFile import ThreadSafeFile
  sys.stdout = ThreadSafeFile(sys.stdout)
except:
  print "! Warning: Threadsafe printing unavailable. Output may be interleaved"

NORMAL = 1
EMULATE = 2
SEARCH = None

# only import serial if a serial device is turned on
if settings.RFID_SCANNER == NORMAL or settings.DISPENSER == NORMAL:
  import serial

## Socket Set-Up
HOST = socket.gethostbyname(socket.gethostname())
PHONE_PORT = 8636
MONEY_PORT = 8637
EMU_RFID_PORT = 8638

try:
  phone_listener = socket.socket()
  phone_listener.bind(("", PHONE_PORT)) #Windows Phone can't connect while debugging if I pass HOST
  phone_listener.listen(1)
  phone_sock = None

  money_listener = socket.socket()
  money_listener.bind(("127.0.0.1", MONEY_PORT))
  money_listener.listen(1)
  money_sock = None

  if settings.RFID_SCANNER == EMULATE:
    rfid_listener = socket.socket()
    rfid_listener.bind(("127.0.0.1", EMU_RFID_PORT))
    rfid_listener.listen(1)
    rfid_sock = None
  
except socket.error as e:
  if e.errno == 10048:
    raw_input("""!! Fatal Error: Socket already in use. Close all other instances of this server
!! and then restart it. If you don't have any visible instances open, try
!! checking for python.exe instances in the task manager.
[ENTER] to exit.""")
    exit()
  else:
    print e.errno
    raise e

## Serial Set-UP
if settings.RFID_SCANNER == NORMAL and type(settings.RFID_SCANNER_COMPORT) == int:
  RFID_SCANNER_COMPORT = serial.device(settings.RFID_SCANNER_COMPORT - 1)
if settings.DISPENSER == NORMAL and type(settings.DISPENSER_COMPORT) == int:
  settings.DISPENSER_COMPORT = serial.device(settings.DISPENSER_COMPORT - 1)

rfid_serial = None
rfid_device = None
dispenser_serial = None
dispenser_device = None

## Subprocess Set-Up
money_process = None
def start_money():
  global money_process
  if settings.BILL_ACCEPTOR == NORMAL and not money_process:
    money_process = subprocess.Popen(["../Munay/bin/Release/Munay.exe"],
                                     creationflags = \
                                                  subprocess.CREATE_NEW_CONSOLE)
def close_money():
  global money_process
  if settings.BILL_ACCEPTOR == NORMAL and money_process:
    money_process.terminate()
    money_process = None
    
## account
account_manager = None
print_relogin_message = False

## Helpers
# helper function to listen for a serial connection on a port
def get_serial(n, wait = 1, get_timeout = None, **kwargs):
  if timeout:
    end = time.time() + get_timeout
  while True:
    try:
      s = serial.Serial(n, **kwargs)
      return s
    except serial.SerialException:
      if get_timeout and time.time() + wait > end:
        return
      time.sleep(wait)

def sanitize_chr(c):
  o = ord(c)
  return chr(o if 32 <= o < 127 else 63)

def sanitize(string):
  return ''.join(map(sanitize_chr, string))

def exit_handler():
  money_thread._Thread__stop()
  if money_process:
    money_process.terminate()
  phone_thread._Thread__stop()
  rfid_thread._Thread__stop()
  dispenser_thread._Thread__stop()
  exit()

## Main Control Structures

# listen to phone
def phone_receiver():
  global phone_sock
  while True:
    # connection
    print "Waiting for phone client"
    phone_sock, address = phone_listener.accept()
    print "Phone client connected from ", address
    while True:
      # wait for message
      try:
        message = phone_sock.recv(512).rstrip()
        if len(message) == 0: # disconnected
          break
      except: # disconnected
        break
      handle_phone_message(message)
    #if program is here, phone client has disconnected
    print "Phone client disconnected"
    phone_sock = None
    account_manager.log_out()

def send_vend_failure(reason, vendId):
  phone_sock.send(json.dumps({'type' : 'vend failure',
                              'reason' : reason,
                              'vendId' : vendId})+"\n")

class BadRequest(Exception): pass
def handle_phone_message(message):
  try:
    request = json.loads(message)
  except:
    print "! Anomolous message from phone client: %s" % message
    return
  if not 'type' in request:
    print "Bad request from phone"
  try:
    if request['type'] == "guest":
      account_manager.log_in_guest()
      print "Logging in as guest"
    if request['type'] == "log out":
      log_out()
    elif request['type'] == "vend":
      try:
        try:
          buy_item(request['vendId'])
        except BadItem:
          send_vend_failure('vendId', request['vendId'])
          return
        except InsufficientFunds:
          send_vend_failure('balance', request['vendId'])
          return
        except SoldOut:
          send_vend_failure('quantity', request['vendId'])
          return
      except URLOpenError as e:
        print "[Error] Could not connect to http://my.studentrnd.org/"
        send_vend_failure('error', request['vendId'])
        return
      except JSONDecodeError as e:
        print "Invalid credentials"
        send_vend_failure('error', request['vendId'])
        return
      except Exception as e:
        print "! Error handling 'vend' request'"
        print "! Error Type: " + e.__class__.__name__
        print "! Error Message: " + e.message
        send_vend_failure('error', request['vendId'])
        return
      
      # return a 'vend success' response
      phone_sock.send(json.dumps({"type" : "vend success",
                                  "balance" : account_manager.balance})+"\n")
    elif request['type'] == "inventory":
      send_inventory(request['key'] if 'key' in request else None)
  except KeyError as e:
    print "Bad '%s' request from phone: '%s' not found in request" % (request['key'],
                                                                      e[0])

def log_out():
  account_manager.log_out()
  print "Logged out."
  try:
    money_sock.send("disable\n")
  except socket.error:
    print "[ERROR] failed to communicate with bill acceptor controller"
  close_money()

# listen to money controller
def money_receiver():
  global money_listener, money_sock
  while True: # main loop
    print "Waiting for money controller"
    money_sock, address = money_listener.accept() # wait for a connection
    print "Money client connection from ", address
    if account_manager.logged_in():
      money_sock.send('enable\n')
    while True: # recieve loop
      try:
        message = money_sock.recv(500).rstrip() # wait for a message
        if len(message) == 0: # disconnected
          break
      except: # connection error
        break
      try:
        amount = int(message)
      except ValueError:
        print "Anomolous message from money client: " + message
        continue
      accept_money(amount)
    #if the program is here, money client has disconnected
    print "Money client disconnected"
    money_sock = None

def accept_money(amount):
  global money_sock, phone_sock
  if account_manager.logged_in():
    account_manager.deposit(amount)
    
    print "Deposited $" + str(amount) + \
         " into " +  account_manager.username + "'s account." + \
         " New balance: $" + str(account_manager.balance)
    response = json.dumps({"type" : "balance update",
                           "balance" : account_manager.balance})
    try:
      phone_sock.send(response+"\n")
    except:
      print "[WARNING] failed to communicate with phone"
  else: # this shouldn't happen, the bill acceptor is disabled while not logged in
    print message + " dollars inserted; ejecting because user not logged in"
    try: # tell money client to return bill and disable the acceptor
      money_sock.send("return\n")
      money_sock.send("disable\n")
    except:
      print "[WARNING] failed to tell money client to return bills"

#listen to rfid scanner
def rfid_receiver():
  global phone_sock, money_sock, rfid_serial, rfid_device, dispenser_device, \
         rfid_listener, rfid_sock
  while True:

    # a real rfid scanner
    if settings.RFID_SCANNER == NORMAL:
      
      # setup serial device
      if settings.RFID_SCANNER_COMPORT: # if specified in settings, as it should be
        print "Waiting for RFID scanner"
        rfid_serial = get_serial(settings.RFID_SCANNER_COMPORT, 4,
                                 baudrate = 2400)
        rfid_device = settings.RFID_SCANNER_COMPORT
        
      else: # hopefully not used
        print "Looking for RFID scanner"
        while not rfid_serial:
          for i in range(1, 10):
            try:
              device = serial.device(i)
              if device != dispenser_device:
                rfid_serial = serial.Serial(device)
                rfid_device = device
                break
            except serial.SerialException:
              continue
          
      try:
        rfid_serial.setDTR(False)
      except serial.SerialException:
        continue
      
      print "Connected to RFID scanner"
    else: #emulated
      print "Waiting for RFID scanner emulator"
      rfid_sock, address = rfid_listener.accept()
      print "RFID Scanner emulator client connected from ", address
      
    while True:

      if settings.RFID_SCANNER == NORMAL:
        try:
          rfid_serial.flushInput()
          rfid_serial.setDTR(True)
          rfid = rfid_serial.read(12).strip()
          rfid_serial.setDTR(False)
        except serial.SerialException:
          break
        
      else: # emulated
        try:
          rfid = rfid_sock.recv(500).strip()
          if len(rfid) == 0:
            break
        except:
          break

      #handle rfid tag
      if phone_sock:
        if rfid == account_manager.rfid:
          if print_relogin_message:
            print "Already logged in as " + account_manager.username
            print_relogin_message = False
          continue
        if account_manager.log_in(rfid):
          print_relogin_message = True
          response  = {"type" : "log in",
                       "username" : account_manager.username,
                       "balance" : account_manager.balance}
          start_money()
          phone_sock.send(json.dumps(response)+"\n")
          print "Logged in as " + account_manager.username
          try:
            money_sock.send("enable\n")
          except:
            print "[ERROR] failed to enable the bill acceptor"
        #else invalid rfid tag, or currently logged in as guest
      #else not connected to client
    print "Disconnected from RFID scanner."

def make_item(vendId, price, quantity, name):
  return {"vendId" : str(vendId).zfill(2),
          "price" : str(price),
          "quantity" : str(quantity),
          "name" : sanitize(name)}

def send_inventory(key):
  db_key = database.get_db_key()
  if db_key != None and key != None and key == db_key:
    phone_sock.send(json.dumps({"type" : "inventory",
                                "inventory" : {"key" : db_key}})+"\n")
  else:
    categories = list()
    for item in database.get_items(order_by = "category"):
      cat_name = sanitize(item[4])
      if len(categories) == 0 or categories[-1]['name'] != cat_name:
        categories.append({"name" : cat_name, "items" : list()})
      categories[-1]['items'].append(make_item(*item[0:4]))
    phone_sock.send(json.dumps({"type" : "inventory",
                                "inventory" : {"key" : db_key,
                                               "categories" : categories}})+"\n")

# dispenser_controller does not communicate with the dispenser (dispenser_serial)
# it only connects and checks the connection.
# It is not run if settings.DISPENSER == EMULATE
def dispenser_controller():
  global dispenser_serial, rfid_device, dispenser_device
  while True:
    if settings.DISPENSER_COMPORT:
      print "Waiting for vending machine controller"
      dispenser_serial = get_serial(settings.DISPENSER_COMPORT)
      dispenser_device = settings.DISPENSER_COMPORT
    else:
      print "Looking for vending machine controller"
      dispenser_serial = None
      while not dispenser_serial:
        for i in range(1, 10):
          try:
            device = serial.device(i)
            if device != rfid_device:
              dispenser_serial = serial.Serial(device)
              dispenser_device = device
              break
          except serial.SerialException:
            continue
    print "Connected to vending machine controller"

    while True:
      try:
        if len(dispenser_serial.read(512)) == 0:
          break
      except:
        break
      time.sleep(3)

#buy_item actually communicates with dispenser controller
def buy_item(vendId):
  global dispenser_serial, phone_sock

  row = database.get_item(vendId)
  if not row:
    raise BadItem()
  price, quantity, name, cat = row
  if quantity < 1:
    raise SoldOut()

  account_manager.withdraw(price, "Vending machine purchase: " + name)
  
  if account_manager.account_type > AccountManager.TEST:
    database.vend_item(vendId)

  # vend the item
  print "Dispensing item " + vendId
  if dispenser_serial:
    dispenser_serial.write("I" + vendId)

def main():
  global account_manager
  print "Starting server on %s." % HOST
  
  account_manager = AccountManager()
  database.connect()

  money_thread = threading.Thread(target = money_receiver)
  phone_thread = threading.Thread(target = phone_receiver)
  rfid_thread = threading.Thread(target = rfid_receiver)
  dispenser_thread = threading.Thread(target = dispenser_controller)

  money_thread.start()
  phone_thread.start()
  rfid_thread.start()
  if settings.DISPENSER == NORMAL:
    dispenser_thread.start()

if __name__ == '__main__':
  main()
  atexit.register(exit_handler)
