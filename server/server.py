#!/usr/bin/env python2.7
print "Loading..."

# system imports
import atexit, codecs, hashlib, json, math, os, random, socket, subprocess, \
       sys, threading, time, urllib
# local imports
import database

if os.path.exists('settings.py'):
  import settings
elif os.path.exists('settings_default.py'):
  import settings_default as settings
  print """! Warning: Using default settings file.
! Please copy `settings_default.py` as `settings.py` and edit it as needed,
! especially DISPENSER_COMPORT and RFID_SCANNER_COMPORT. If you do not specify
! these to COM ports, this program is not guaranteed to function properly"""
else:
  print "!! Fatal Error: Couldn't find settings file or default setting file."
  raw_input("[ENTER] to exit.")
  exit()

if os.path.exists('credentials.py'):
  import credentials
else:
  raw_input("""!! Fatal Error: Couldn't find credentials file.
!! Please copy `credentials_default.py` as `credentials.py` and add the Vending
!! Machine credentials.
[ENTER] to exit.""")
  exit()

NORMAL = settings.NORMAL
EMULATE = settings.EMULATE
# I'm lazy and didn't want to refactor everything.
RFID_SCANNER = settings.RFID_SCANNER
RFID_SCANNER_COMPORT = settings.RFID_SCANNER_COMPORT
DISPENSER = settings.DISPENSER
DISPENSER_COMPORT = settings.DISPENSER_COMPORT
BILL_ACCEPTOR = settings.BILL_ACCEPTOR

try:
  from ThreadSafeFile import ThreadSafeFile
  sys.stdout = ThreadSafeFile(sys.stdout)
except:
  print "! Warning: Threadsafe printing unavailable. Output may be interleaved"

# only import serial if a serial device is turned on
if RFID_SCANNER == NORMAL or DISPENSER == NORMAL:
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

  if RFID_SCANNER == EMULATE:
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
if RFID_SCANNER == NORMAL and type(RFID_SCANNER_COMPORT) == int:
  RFID_SCANNER_COMPORT = serial.device(RFID_SCANNER_COMPORT - 1)
if DISPENSER == NORMAL and type(DISPENSER_COMPORT) == int:
  DISPENSER_COMPORT = serial.device(DISPENSER_COMPORT - 1)

rfid_serial = None
rfid_device = None
dispenser_serial = None
dispenser_device = None

## Subprocess Set-Up
money_process = None
def start_money():
  global money_process
  if BILL_ACCEPTOR == NORMAL and not money_process:
    money_process = subprocess.Popen(["../Munay/bin/Release/Munay.exe"],
                                     creationflags = \
                                                  subprocess.CREATE_NEW_CONSOLE)
def close_money():
  global money_process
  if BILL_ACCEPTOR == NORMAL and money_process:
    money_process.terminate()
    money_process = None
    
## Global vars for tracking logged-in status
username = None
cur_rfid = None
balance = None
print_relogin_messsage = False

## Helpers
# helper function to listen for a serial connection on a port
def get_serial(n, wait = 1, timeout = None):
  if timeout:
    end = time.time() + timeout
  while True:
    try:
      s = serial.Serial(n)
      return s
    except serial.SerialException:
      if timeout and time.time() + wait > end:
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
    if username:
      log_out()

class InsufficientFunds(Exception): pass
class SoldOut(Exception): pass
class BadItem(Exception): pass
class BadRequest(Exception): pass
def handle_phone_message(message):
  try:
    request = json.loads(message)
  except:
    print "! Anomolous message from phone client: %s" % message
    return
  if not 'type' in request:
    print "Bad request from phone"
  if request['type'] == "log out":
    log_out()
  elif request['type'] == "vend":
    try:
      if 'vendId' in request:
        dispense_item(request['vendId'])
      else: raise BadRequest("'vendId' not found in request")
    except InsufficientFunds:
      phone_sock.send(json.dumps({'type' : 'vend failure',
                                  'reason' : 'balance'})+"\n")
    except SoldOut:
      phone_sock.send(json.dumps({'type' : 'vend failure',
                                  'reason' : 'quantity'})+"\n")
    except BadItem:
      phone_sock.send(json.dumps({'type' : 'vend failure',
                                  'reason' : 'vendId'})+"\n")
    except Exception as e:
      print "! Error handling 'vend' request'"
      print "! Error Type: " + e.__class__.__name__
      print "! Error Message: " + e.message
      phone_sock.send(json.dumps({'type' : 'vend failure',
                                  'reason' : 'error',
                                  'vendId' : request['vendId']})+"\n")
  elif request['type'] == "inventory":
    send_inventory(request['key'] if 'key' in request else None)

def log_out():
  global username, cur_rfid, balance
  print "Logging out"
  username = None
  cur_rfid = None
  balance = None
  try:
    money_sock.send("disable\n")
  except:
    print "[ERROR] failed to communicate with bill acceptor controller"
  close_money()

# listen to money controller
def money_receiver():
  global money_listener, money_sock, username
  while True: # main loop
    print "Waiting for money controller"
    money_sock, address = money_listener.accept() # wait for a connection
    print "Money client connection from ", address
    if username:
      money_sock.send('enable\n')
    while True: # recieve loop
      try:
        message = money_sock.recv(500).rstrip() # wait for a message
        if len(message) == 0: # disconnected
          break
      except: # connection error
        break
      accept_money(message)
    #if the program is here, money client has disconnected
    print "Money client disconnected"
    money_sock = None

def accept_money(message):
  global money_sock, phone_sock, username, balance
  try: # is message an int? (the only way it isn't right now is through emulation)
    amount = int(message)
  except ValueError:
    print "Anomolous message from money client: " + message
    return
  if username:
    if cur_rfid == settings.TESTING_RFID:
      balance += amount
    else:
      curtime = str(int(time.time()))
      rand = random.randint(0, math.pow(2, 32) - 1)
      sig = hashlib.sha256(str(curtime) + str(rand) + credentials.PRIVATE_KEY).hexdigest()

      url = "http://my.studentrnd.org/api/balance/eft"
      get = urllib.urlencode({"application_id" : credentials.APP_ID,
                              "time" : curtime,
                              "nonce" : str(rand),
                              "username" : username,
                              "signature" : sig})
      post = urllib.urlencode({'username' : username,
                               'amount': message,
                               'description': "vending machine deposit",
                               'type': 'deposit'})
      
      response = urllib.urlopen(url + '?' + get, post).read()
      balance = str(json.loads(response)['balance'])
      
    print "Deposited $" + message + " into " + username + "'s account. New balance: $" + balance
    response = json.dumps({"type" : "balance update",
                           "balance" : balance})
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
  global phone_sock, money_sock, rfid_serial, rfid_device, dispenser_device, username, \
         cur_rfid, rfid_listener, rfid_sock
  while True:

    # a real rfid scanner
    if RFID_SCANNER == NORMAL:
      
      # setup serial device
      if RFID_SCANNER_COMPORT: # if specified in settings, as it should be
        print "Waiting for RFID scanner"
        rfid_serial = get_serial(RFID_SCANNER_COMPORT, 4)
        rfid_device = RFID_SCANNER_COMPORT
        
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
        rfid_serial.baudrate = 2400
      except serial.SerialException: continue
      
      print "Connected to RFID scanner"
    else: #emulated
      print "Waiting for RFID scanner emulator"
      rfid_sock, address = rfid_listener.accept()
      print "RFID Scanner emulator client connected from ", address
      
    while True:

      if RFID_SCANNER == NORMAL:
        try:
          rfid_serial.flushInput()
          rfid_serial.setDTR(True)
          rfid = rfid_serial.read(12).strip()
          rfid_serial.setDTR(False)
        except serial.SerialException:
          break
        
      else: # emulated
        try:
          rfid = rfid_sock.recv(500).rstrip()
          if len(rfid) == 0:
            break
        except:
          break
      if phone_sock:
        handle_rfid_tag(rfid)
    print "Disconnected from RFID scanner."

def handle_rfid_tag(rfid):
  global username, cur_rfid, phone_sock, money_sock, balance, print_relogin_message
  if rfid == cur_rfid:
    if print_relogin_message:
      print "already logged in as " + username
      print_relogin_message = False
    return

  if rfid == settings.TESTING_RFID:
    username = settings.TESTING_USERNAME
    cur_rfid = rfid
    balance = settings.TESTING_BALANCE
  else:
    curtime = str(int(time.time()))
    rand = random.randint(0, math.pow(2, 32) - 1)
    sig = hashlib.sha256(str(curtime) + str(rand) + credentials.PRIVATE_KEY).hexdigest()
    try:
      response = urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + rfid).read()
    except IOError as e:
      if e.strerror.errno == 11004:
        print "[Error] Could not connect to http://my.studentrnd.org/"
        return
      else:
        raise e
    try:
      username = json.loads(response)['username']
      cur_rfid = rfid
      print_relogin_message = True
    except ValueError:
      print "Unknown RFID tag: %s" % rfid
      return
    
    url  = "http://my.studentrnd.org/api/balance"
    data = urllib.urlencode((("application_id", credentials.APP_ID),
                             ("time", str(curtime)),
                             ("nonce", str(rand)),
                             ("username", username),
                             ("signature", sig)))
    try:
      balance = json.loads(urllib.urlopen(url + '?' + data).read())['balance']
    except ValueError:
      print "Invalid credentials"
      return

  response  = {"type" : "log in",
               "username" : username,
               "balance" : float(balance)}

  start_money()
  phone_sock.send(json.dumps(response)+"\n")
  print "Logged in: " + username
  try:
    money_sock.send("enable\n")
  except:
    print "[ERROR] failed to enable the bill acceptor"
    # display on phone? notify someone?

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
# It is not run if DISPENSER == EMULATE
def dispenser_controller():
  global dispenser_serial, rfid_device, dispenser_device
  while True:
    if DISPENSER_COMPORT:
      print "Waiting for vending machine controller"
      dispenser_serial = get_serial(DISPENSER_COMPORT)
      dispenser_device = DISPENSER_COMPORT
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

#dispense_item actually communicates with dispenser controller
def dispense_item(vendId):
  global dispenser_serial, username, phone_sock, balance

  row = database.get_item(vendId)
  if not row:
    raise BadItem()
  price, quantity, name = row[:-1]
  if quantity < 1:
    raise SoldOut()
  if price > balance:
    raise InsufficientFunds()
  if cur_rfid != settings.TESTING_RFID:
    database.vend_item(vendId)

  # vend the item
  print "Dispensing item " + vendId
  if dispenser_serial:
    dispenser_serial.write("I" + vendId)

  # update balance
  if cur_rfid == settings.TESTING_RFID:
    balance -= float(price)
  else:
    curtime = str(int(time.time()))
    rand = random.randint(0, math.pow(2, 32) - 1)
    sig = hashlib.sha256(str(curtime) + str(rand) + credentials.PRIVATE_KEY).hexdigest()
    
    url = "http://my.studentrnd.org/api/balance/eft"
    get = urllib.urlencode({"application_id": credentials.APP_ID,
                            "time" : curtime,
                            "nonce" : rand,
                            "username" : username,
                            "signature" : sig})
    post = urllib.urlencode({'username' : username,
                             'amount': price,
                             'description': "Vending machine purchase: " + name,
                             'type': 'withdrawl'})
    response = urllib.urlopen(url + '?' + get, post).read()
    balance = json.loads(response)['balance']

  # return a 'vend success' response
  phone_sock.send(json.dumps({"type" : "vend success",
                              "balance" : balance})+"\n")

def main():
  database.connect()
  
  print "Starting server on %s." % HOST

  money_thread = threading.Thread(target = money_receiver)
  phone_thread = threading.Thread(target = phone_receiver)
  rfid_thread = threading.Thread(target = rfid_receiver)
  dispenser_thread = threading.Thread(target = dispenser_controller)

  money_thread.start()
  phone_thread.start()
  rfid_thread.start()
  if DISPENSER == NORMAL:
    dispenser_thread.start()

if __name__ == '__main__':
  main()
  atexit.register(exit_handler)
