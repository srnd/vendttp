#!/usr/bin/env python2.7
print "Loading..."

# settings, etc.
EMULATE = 2
try: from settings import RFID_SCANNER
except: RFID_SCANNER = 1
try: from settings import RFID_SCANNER_COMPORT
except: RFID_SCANNER_COMPORT = None
try: from settings import DISPENSER
except: DISPENSER = 1
try: from settings import DISPENSER_COMPORT
except: DISPENSER_COMPORT = None
from credentials import APP_ID, PRIVATE_KEY

# system imports
import sys, socket, string, threading, urllib, json, time, \
       random, hashlib, math, re, sqlite3, subprocess

# installed imports
import serial
from serial import Serial
if RFID_SCANNER == EMULATE or DISPENSER == EMULATE:
  #from emulate import Serial
  raise ValueError("EMULATE is not supported yet")
from lxml.builder import E
from lxml.etree import tostring

HOST="localhost"
PORT=8636
HOST2="localhost"
PORT2=8637

phone_listener = socket.socket()
phone_listener.bind((HOST, PORT))
phone_listener.listen(1)
phone_sock = None
money_listener = socket.socket()
money_listener.bind((HOST2, PORT2))
money_listener.listen(1)
money_sock = None

if type(RFID_SCANNER_COMPORT) == int:
  RFID_SCANNER_COMPORT = serial.device(RFID_SCANNER_COMPORT - 1)
if type(DISPENSER_COMPORT) == int:
  DISPENSER_COMPORT = serial.device(DISPENSER_COMPORT - 1)

ser = None
serdevice = None
ser2 = None
serdevice2 = None

username = ""
cur_rfid = ""
itemqueue = []

#junk to put somewhere maybe
def get_serial(n, wait = 1, timeout = None):
  if timeout:
    now = time.time()
    then = now + timeout
  while True:
    try:
      s = Serial(n)
      return s
    except serial.SerialException:
      if timeout and time.time() + wait > then:
        return
      time.sleep(wait)

def send():
  global phone_sock
  while True:
    message = raw_input()
    try:
      phone_sock.send(message)
    except:
      s = "[ERROR] cannot send"
      if phone_sock == None:
        s += ", phone clinet not connected"
      print s

def phone_receiver():
  global phone_listener, phone_sock, money_sock, \
         username, itemqueue, cur_rfid, ser2
  while True:
    phone_sock, address = phone_listener.accept()
    print "Phone client connected from ", address
    while True:
      try:
        message = phone_sock.recv(500).rstrip()
        if len(message) == 0:
          break
      except:
        break
      pstuff = re.search("^[iI](?P<id>\d\d)", message)
      if message == "logout":
        username = ""
        cur_rfid = ""
        try:
          money_sock.send("disable")
        except:
          print "[ERROR] failed to communicate with bill acceptor"
      elif pstuff and username != "":
        DispenseItem(pstuff.group("id"))
#        ser2.write("I" + pstuff.group("id"))
#        itemqueue[len(itemqueue)] = pstuff.group("id")

      else:
        print message
    #if program is here, phone client has disconnected
    print "Phone client disconnected"
    phone_sock = None


def money_receiver():
  global phone_sock, money_listener, money_sock, username

  while True: # main loop
    money_sock, address = money_listener.accept() # wait for a connection
    print "Money client connection from ", address
    while True: # recieve loop
      try:
        message = money_sock.recv(500).rstrip() # wait for a message
        if len(message) == 0: # i.e. disconnected
          break
      except: # i.e. connection error
        break
      try: # is message an int? (the only way it isn't right now is through emulation)
        amount = int(message)
      except ValueError:
        print "Anomolous message from money client: " + message
        continue # go back and wait for message
      if username != "":
        curtime = str(int(time.time()))
        rand = random.randint(0, math.pow(2, 32) - 1)

        url = "http://my.studentrnd.org/api/balance/eft?application_id=" + APP_ID
        url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
        url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + PRIVATE_KEY).hexdigest()

        data = {'username': username,
                'amount': str(message),
                'description': "[Test] Vending Machine deposit",
                'type': 'deposit'}
        
        nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])
        print "Deposited $" + message + " into " + username + "'s account. New balance: $" + nbalance

        response = E('response', type = 'balanceUpdate')
        response.append(E('balance', nbalance))
        try:
          phone_sock.send(tostring(response))
        except:
          print "[WARNING] failed to communicate with phone"
        
      else: # this shouldn't happen, the bill acceptor is disabled while not logged in
        print message + " dollars inserted; ejecting because user not logged in"
        try: # tell money client to return bill and disable the acceptor
          money_sock.send("return")
          money_sock.send("disable")
        except:
          print "[WARNING] failed to tell money client to return bills"
    #if the program is here, money client has disconnected
    print "Money client disconnected"
    money_sock = None


def rfid_receiver():
  global phone_sock, money_sock, ser, serdevice, serdevice2, username, cur_rfid
  while True:
    if RFID_SCANNER_COMPORT:
      print "Waiting for RFID scanner"
      ser = get_serial(RFID_SCANNER_COMPORT)
      serdevice = RFID_SCANNER_COMPORT
    else:
      print "Looking for RFID scanner"
      while True:
        for i in range(1, 10):
          try:
            device = serial.device(i)
            if device != serdevice2:
              ser = Serial(device)
              ser.baudrate = 2400
              serdevice = device
              break
          except serial.SerialException:
            continue
        if ser: #TODO: check that it is, in fact, the RFID scanner
          break
    print "Connected to RFID scanner"
    try:
      ser.setDTR(False)
    except serial.SerialException:
      print "Disconnected from RFID scanner"
      continue
    while True:
      try:
        ser.flushInput()
        ser.setDTR(True)
        rfid = ""
        i = ''
        while i != '\r':
          i = ser.read()
          if i != '\n' and i != '\r':
            rfid = rfid + i
        ser.setDTR(False)
      except serial.SerialException:
        break

      if rfid == cur_rfid:
        print "already logged in as " + username
        time.sleep(3)
        continue

      if rfid == "0300BECB2E": # test tag
        username = "tyler.menezes"
      else:
        curtime = str(int(time.time()))
        rand = random.randint(0, math.pow(2, 32) - 1)
        response = urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + rfid).read()
        try:
          username = json.loads(response)['username']
        except ValueError:
          print "Unknown RFID tag"
          time.sleep(3)
          continue
      
      cur_rfid = rfid
      
      url  = "http://my.studentrnd.org/api/balance?application_id=" + APP_ID
      url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
      url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + \
                                            PRIVATE_KEY).hexdigest()

      balance = json.loads(urllib.urlopen(url).read())['balance']

      response = E('response',
                   type = 'inventory')
      response.append(E('account',
                        name = username.replace(".", " "),
                        balance = str(balance)))

      conn = sqlite3.connect('items.sqlite')
      c = conn.cursor()
      c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id integer primary key, vendId text, price numeric, quantity numeric, name text, category text)''')
      conn.commit()

      catagories = {}
      for item in c.execute("SELECT * from items ORDER BY id"):
        if item[5] in catagories:
          catagories[item[5]].append(E('item',
                                       id = str(item[0]),
                                       vendId = str(item[1]),
                                       price = str(item[2]),
                                       quantity = str(item[3]),
                                       name = item[4]))
        else:
          catagories[item[5]] = [E('item',
                                   id = str(item[0]),
                                   vendId = str(item[1]),
                                   price = str(item[2]),
                                   quantity = str(item[3]),
                                   name = item[4])]

      conn.close()

      response2 = E('response', type='inventory')
      for category, items in catagories.iteritems():
        response2 = E('category', name=category)
        for item in items:
          response2.append(item)

      try:
        phone_sock.send(tostring(response))
        phone_sock.send(tostring(response2))
        print "Logged in: " + username
        try:
          money_sock.send("enable")
        except socket.error:
          print "[ERROR] failed to enable the bill acceptor"
          # display on phone? notify someone?
      except socket.error:
        print "[ERROR] failed to log in. Could not communicate with phone"
      time.sleep(3)
    print "Disconnected from RFID scanner."


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
      while True:
        for i in range(1, 10):
          try:
            device = serial.device(i)
            if device != serdevice:
              ser2 = Serial(device)
              serdevice2 = device
              break
          except serial.SerialException:
            continue
        if ser2: # TODO: check that it is, in fact, the dispensor controller
          break
    print "Connected to vending machine controller"

    while True:
      try:
        if len(ser2.read()) == 0:
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

  if item[3] == 0:
    return False

  curtime = str(int(time.time()))
  rand = random.randint(0, math.pow(2, 32) - 1)

  url = "http://my.studentrnd.org/api/balance/eft?application_id=" + APP_ID

  url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

  sig = hashlib.sha256(str(curtime) + str(rand) + PRIVATE_KEY).hexdigest()

  url += sig

  data = {'username': username, 'amount': str(item[2]), 'description': "[Test] Vending machine purchase: " + item[4], 'type': 'withdrawl'}

  nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

  phone_sock.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")

  c.execute("UPDATE items SET quantity = ? WHERE vendId = ?", [item[3] - 1, id])
  conn.commit()

  conn.close()

  print "Dispensing item " + id
  ser2.write("I" + id)


print "Starting server.\nWaiting for clients"

threading.Thread(target = money_receiver).start()
threading.Thread(target = phone_receiver).start()
threading.Thread(target = send).start()

if RFID_SCANNER:
  threading.Thread(target = rfid_receiver).start()
  time.sleep(2) #for now; so that the rfid thread connects first. We assume that the rfid scanner is on a lower comport.
if DISPENSER:
  threading.Thread(target = dispenser_controller).start()
