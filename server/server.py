#!/usr/bin/env python2.7
print "Loading..."

try:
  with open('settings.py'): pass
except:
  try:
    with open('settings_default.py'):
      import shutil
      print "Using default settings file..."
      shutil.copyfile('settings_default.py', 'settings.py')
  except:
    print "Couldn't load settings file."

try:
  with open('credentials.py'): pass
except:
  try:
    with open('credentials_default.py'):
      import shutil
      print "Using default credentials file..."
      shutil.copyfile('credentials_default.py', 'credentials.py')
  except:
    traceback.print_exc(50)
    print "Couldn't load credentials file."
    raw_input("[ENTER] to exit")
 

OFF = 0
ON = 1
EMULATE = 2
# settings, etc.
try: from settings import RFID_SCANNER
except: RFID_SCANNER = ON
try: from settings import RFID_SCANNER_COMPORT
except: RFID_SCANNER_COMPORT = None
try: from settings import DISPENSER
except: DISPENSER = ON
try: from settings import DISPENSER_COMPORT
except: DISPENSER_COMPORT = None
try: from credentials import APP_ID, PRIVATE_KEY
except: pass

# system imports
import sys, socket, string, threading, urllib, json, time, \
       random, hashlib, math, re, sqlite3, subprocess

try:
  from ThreadSafeFile import ThreadSafeFile
  sys.stdout = ThreadSafeFile(sys.stdout)
except:
  print "Threadsafe printing unavailable. Output may be interleaved"

# only import serial if a serial device is turned on
if RFID_SCANNER == ON or DISPENSER == ON:
  import serial

## Socket Set-Up
HOST=socket.gethostbyname(socket.gethostname())
PORT=8636
HOST2="localhost"
PORT2=8637
EMURFIDPORT=8638

phone_listener = socket.socket()
phone_listener.bind(("", PORT)) #Windows Phone can't connect if I pass HOST
phone_listener.listen(1)
phone_sock = None

money_listener = socket.socket()
money_listener.bind((HOST2, PORT2))
money_listener.listen(1)
money_sock = None

if RFID_SCANNER == EMULATE:
  rfid_listener = socket.socket()
  rfid_listener.bind((HOST2, EMURFIDPORT))
  rfid_listener.listen(1)
  rfid_sock = None

## Serial Set-UP
if RFID_SCANNER == ON and type(RFID_SCANNER_COMPORT) == int:
  RFID_SCANNER_COMPORT = serial.device(RFID_SCANNER_COMPORT - 1)
if DISPENSER == ON and type(DISPENSER_COMPORT) == int:
  DISPENSER_COMPORT = serial.device(DISPENSER_COMPORT - 1)

ser = None
serdevice = None
ser2 = None
serdevice2 = None

munay_process = None

## Global to check logged-in status
username = ""
cur_rfid = ""

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

# start the money client
def start_munay():
  munay_process = subprocess.Popen("Munay/bin/Debug/Munay.exe")

def close_munay():
  munay_process.kill()

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

def handle_phone_message(message):
  pstuff = re.search("^[iI](?P<id>\d\d)", message)
  if message == "logout":
    log_out()
  elif pstuff and username != "":
    DispenseItem(pstuff.group("id"))
  else:
    print message

def log_out():
  global username, cur_rfid
  print "Logging out"
  username = ""
  cur_rfid = ""
  try:
    money_sock.send("disable")
    close_munay()
  except:
    print "[ERROR] failed to communicate with bill acceptor controller"

# listen to money controller
def money_receiver():
  global money_listener, money_sock, username
  while True: # main loop
    print "Waiting for money controller"
    money_sock, address = money_listener.accept() # wait for a connection
    print "Money client connection from ", address
    if username:
      money_sock.send('enable')
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
  global money_sock, phone_sock, username
  try: # is message an int? (the only way it isn't right now is through emulation)
    amount = int(message)
  except ValueError:
    print "Anomolous message from money client: " + message
    return
  if username:
    curtime = str(int(time.time()))
    rand = random.randint(0, math.pow(2, 32) - 1)

    url = "http://my.studentrnd.org/api/balance/eft?application_id=" + APP_ID
    url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
    url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + PRIVATE_KEY).hexdigest()

    data = {'username': username,
            'amount': str(message),
            'description': "vending machine deposit",
            'type': 'deposit'}
    
    nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])
    print "Deposited $" + message + " into " + username + "'s account. New balance: $" + nbalance

    response = "<response type=\"balanceUpdate\">"
    response += "<balance>" + nbalance + "</balance>"
    response += "</response>"
    try:
      phone_sock.send(response)
    except:
      print "[WARNING] failed to communicate with phone"
    
  else: # this shouldn't happen, the bill acceptor is disabled while not logged in
    print message + " dollars inserted; ejecting because user not logged in"
    try: # tell money client to return bill and disable the acceptor
      money_sock.send("return")
      money_sock.send("disable")
    except:
      print "[WARNING] failed to tell money client to return bills"

def rfid_receiver():
  global phone_sock, money_sock, ser, serdevice, serdevice2, username, \
         cur_rfid, rfid_listener, rfid_sock
  while True:

    # a real rfid scanner
    if RFID_SCANNER != EMULATE:
      
      # setup serial device
      if RFID_SCANNER_COMPORT: # if specified in settings, as it should be
        print "Waiting for RFID scanner"
        ser = get_serial(RFID_SCANNER_COMPORT, 4)
        serdevice = RFID_SCANNER_COMPORT\
        
      else: # hopefully not used
        print "Looking for RFID scanner"
        while not ser:
          for i in range(1, 10):
            try:
              device = serial.device(i)
              if device != serdevice2:
                ser = serial.Serial(device)
                serdevice = device
                break
            except serial.SerialException:
              continue
          
      try:
        ser.setDTR(False)
        ser.baudrate = 2400
      except serial.SerialException: continue
      
      print "Connected to RFID scanner"
    else: #emulated
      print "Waiting for RFID scanner emulator"
      rfid_sock, address = rfid_listener.accept()
      print "RFID Scanner emulator client connected from ", address
      
    while True:

      if RFID_SCANNER != EMULATE:
        try:
          ser.flushInput()
          ser.setDTR(True)
          rfid = ser.read(12).strip()
          ser.setDTR(False)
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
  global username, cur_rfid, phone_sock, money_sock
  if rfid == cur_rfid:
    print "already logged in as " + username
    time.sleep(3)
    return

  curtime = str(int(time.time()))
  rand = random.randint(0, math.pow(2, 32) - 1)
  response = urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + rfid).read()
  try:
    username = json.loads(response)['username']
    cur_rfid = rfid
  except ValueError:
    print "Unknown RFID tag: %s" % rfid
    time.sleep(3)
    return
  
  url  = "http://my.studentrnd.org/api/balance?application_id=" + APP_ID
  url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
  url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + \
                                        PRIVATE_KEY).hexdigest()
  try:
    balance = json.loads(urllib.urlopen(url).read())['balance']
  except ValueError:
    print "Invalid credentials"
    time.sleep(3)
    return

  response = "<response type=\"account\">"
  response += "<account name=\"%s\"" % username.replace(".", " ")
  response += " balance=\"%s\"/>" % balance
  response += "</response>"

  conn = sqlite3.connect('items.sqlite')
  c = conn.cursor()
  c.execute('''CREATE TABLE IF NOT EXISTS items
             (vendId integer primary key, price numeric, quantity numeric, name text, category text)''')
  conn.commit()

  def make_item(vendId, price, quantity, name):
    s  = "<item"
    s += " vendId=\"%02d\"" % vendId
    s += " price=\"%s\"" % price
    s += " quantity=\"%s\"" % quantity
    s += " name=\"%s\"" % name
    s += "/>"
    return s
  
  catagories = {}
  for item in c.execute("SELECT * from items ORDER BY category"):
    if item[4] in catagories:
      catagories[item[4]].append(make_item(*item[0:4]))
    else:
      catagories[item[4]] = [make_item(*item[0:4])]

  conn.close()

  response2 = "<response type=\"inventory\">"
  for category, items in catagories.iteritems():
    response2 += "<category name=\"%s\">" % category
    for item in items:
      response2 += item
    response2 += "</category>"
  response2 += "</response>"

  try:
    start_munay()
    phone_sock.send(response)
    phone_sock.send(response2)
    print "Logged in: " + username
    try:
      money_sock.send("enable")
    except:
      print "[ERROR] failed to enable the bill acceptor"
      # display on phone? notify someone?
  except:
    print "[ERROR] failed to log in. Could not communicate with phone"
    username = ""
    cur_rfid = ""
  time.sleep(3)


# dispenser_controller does not communicate with the dispenser (ser2)
# it only connects and checks the connection
def dispenser_controller():
  global ser2, serdevice, serdevice2
  while True:
    if DISPENSER_COMPORT:
      print "Waiting for vending machine controller"
      ser2 = get_serial(DISPENSER_COMPORT)
      serdevice2 = DISPENSER_COMPORT
    else:
      print "Looking for vending machine controller"
      ser2 = None
      while not ser2:
        for i in range(1, 10):
          try:
            device = serial.device(i)
            if device != serdevice:
              ser2 = serial.Serial(device)
              serdevice2 = device
              break
          except serial.SerialException:
            continue
    print "Connected to vending machine controller"

    while True:
      try:
        if len(ser2.read(512)) == 0:
          break
      except:
        break
      time.sleep(3)

def DispenseItem(id):
  global ser2, username, phone_sock

  conn = sqlite3.connect('items.sqlite')
  c = conn.cursor()
  conn.commit()

  c.execute("SELECT * from items where vendId = ? LIMIT 1", [id])

  item = c.fetchone()

  #if item[3] == 0:
  #  return False

  curtime = str(int(time.time()))
  rand = random.randint(0, math.pow(2, 32) - 1)

  url = "http://my.studentrnd.org/api/balance/eft?application_id=" + APP_ID
  url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="
  sig = hashlib.sha256(str(curtime) + str(rand) + PRIVATE_KEY).hexdigest()
  url += sig
  data = {'username': username, 'amount': str(item[1]), 'description': "[Test] Vending machine purchase: " + item[3], 'type': 'withdrawl'}
  nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

  phone_sock.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")

  c.execute("UPDATE items SET quantity = ? WHERE vendId = ?", [item[2] - 1, id])
  conn.commit()
  conn.close()

  print "Dispensing item " + id
  if ser2:
    ser2.write("I" + id)


print "Starting server on %s." % HOST

money_thread = threading.Thread(target = money_receiver)
phone_thread = threading.Thread(target = phone_receiver)
rfid_thread = threading.Thread(target = rfid_receiver)
dispenser_thread = threading.Thread(target = dispenser_controller)


try:
  money_thread.start()
  phone_thread.start()
  if RFID_SCANNER != OFF:
    rfid_thread.start()
  if DISPENSER == ON:
    dispenser_thread.start()
  while True:
    raw_input()
except (KeyboardInterrupt, EOFError, SystemExit):
  print "Exiting..."
  money_thread._Thread__stop()
  phone_thread._Thread__stop()
  phone_thread._Thread__stop()
  dispenser_thread._Thread__stop()
  sys.exit()
