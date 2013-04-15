#!/usr/bin/env python2.7
print "Loading..."
EMULATE = 2

try: from settings import BILL_ACCEPTOR
except: BILL_ACCEPTOR = 1
try: from settings import RFID_SCANNER
except: RFID_SCANNER = 1
try: from settings import DISPENSER
except: DISPENSER = 1

import sys, socket, string, threading, urllib, json, \
       time, random, hashlib, math, re, sqlite3
import serial
from serial import Serial
if RFID_SCANNER == EMULATE or DISPENSER == EMULATE:
  #from emulate import Serial
  raise ValueError("EMULATE is only supported for BILL_ACCEPTOR")
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

sernum = 0
ser = None
ser2 = None

username = ""
cur_rfid = ""
itemqueue = []

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

def phone_receive():
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
      pstuff = re.search("^[iI](?P<id>\d\d)$", message)
      if message == "logout":
        username = ""
        cur_rfid = ""
        try:
          money_sock.send("disable")
        except:
          print "[ERROR] failed to communicate with bill acceptor"
      elif pstuff and username != "":
        print "Dispensing item " + pstuff.group("id")
        ser2.write("I" + pstuff.group("id"))
#        itemqueue[len(itemqueue)] = pstuff.group("id")

      else:
        print message
    #if program is here, phone client has disconnected
    print "Phone client disconnected"
    phone_sock = None


def Money():
  global phone_sock, money_listener, money_sock, username

  while True: # main loop
    money_sock, address = money_listener.accept() # wait for a connection
    print "Money client connection from ", address
    while True: # recieve loop
      try:
        message = money_sock.recv(500).rstrip() # wait for a message
        if len(message) == 0: # i.e. disconnected
          break
      except: # i.e. disconnection error
        break
      try: # is message an int? (the only way it isn't right now is through emulation)
        amount = int(message)
      except ValueError:
        print "Anomolous message from money client: " + message
        continue # go back and wait for message
      if username != "":
        curtime = str(int(time.time()))
        rand = random.randint(0, math.pow(2, 32) - 1)

        url = "http://my.studentrnd.org/api/balance/eft?application_id=APP_ID_GOES_HERE"
        url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="
        url += hashlib.sha256(str(curtime) + str(rand) + \
                              "PRIVATE_KEY_GOES_HERE").hexdigest()

        data = {'username': username,
                'amount': str(message),
                'description': "[Test] Vending machine deposit",
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


def Com():
  global phone_sock, money_sock, ser, username, cur_rfid
  for i in range(1, 10):
    try:
      ser = Serial(i)
      ser.baudrate = 2400
      sernum = i
      break
    except serial.SerialException:
      continue

  if ser == None:
    print "No RFID scanner detected. Exiting..."
    return
  else:
    print "Connected to RFID scanner"
  # TODO: fix this so it waits for the connection
  
  ser.setDTR(False)
  while True:
    debug = False
    ser.flushInput()
    ser.setDTR(True)
    rfid = ""
    i = ''
    while i != '\r':
      i = ser.read()
      if i != '\n' and i != '\r':
        rfid = rfid + i
    ser.setDTR(False)

    if rfid == cur_rfid:
      print "already logged in as " + username
      time.sleep(3)
      continue

    curtime = str(int(time.time()))
    rand = random.randint(0, math.pow(2, 32) - 1)
    response = urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + rfid).read()
    try:
      username = json.loads(response)['username']
    except ValueError:
      if rfid != "0300BECB2E":
        print "Unknown RFID tag"
        time.sleep(3)
        continue
      else:
        print "Debug RFID tag detected"
        debug = True

    url  = "http://my.studentrnd.org/api/balance?application_id=APP_ID_GOES_HERE"
    url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
    url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + \
                                          "PRIVATE_KEY_GOES_HERE").hexdigest()

    if not debug:
      balance = json.loads(urllib.urlopen(url).read())['balance']
    else:
      balance = 1000

    response = E('response',
                 type = 'inventory')
    response.append(E('account',
                      name = username.replace(".", " "),
                      balance = str(balance)))

    conn = sqlite3.connect('items.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
               (id integer primary key, vendId numeric, price numeric, quantity numeric, name text, category text)''')
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
      cur_rfid = rfid
      try:
        money_sock.send("enable")
      except socket.error:
        print "[ERROR] failed to enable the bill acceptor"
        # display on phone? notify someone?
    except socket.error:
      print "[ERROR] failed to log in. Could not communicate with phone"
    time.sleep(3)


#TODO:  REFACTOR
def Com2():
  global ser, ser2, phone_sock, itemqueue
  
  for i in range(2, 10):
    try:
      ser2 = Serial(i)
      break
    except:
      continue

  if ser2 == None:
    print "Can't connect to vending machine. Exiting..."
    exit()
  else:
    print "Connected to vending machine"
    
  while True:
    if len(itemqueue) != 0:
      print "Item in queue. Dispensing..."
      conn = sqlite3.connect('items.sqlite')
      c = conn.cursor()
      conn.commit()

      for i in itemqueue:
        print "Dispensing item " + i
        c.execute("SELECT * from items where vendId = ? LIMIT 1", int(i))

        item = c.fetchone()
        
#        curtime = str(int(time.time()))
#        rand = random.randint(0, math.pow(2, 32) - 1)

#        url = "http://my.studentrnd.org/api/balance/eft?application_id=APP_ID_GOES_HERE"

#        url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

#        sig = hashlib.sha256(str(curtime) + str(rand) + "PRIVATE_KEY_GOES_HERE").hexdigest()

#        url += sig

#        data = {'username': username, 'amount': str(item[2]), 'description': "[Test] Vending machine purchase: " + item[4], 'type': 'withdrawl'}

#        nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

#        phone_sock.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")

        ser2.write("I" + i)
        
        c.execute("UPDATE items SET quantity = ? WHERE vendId = ? LIMIT 1", item[3] - 1, i)
        conn.commit()

      conn.close()
    time.sleep(1)


print "Starting server. Waiting for clients"

if RFID_SCANNER:
  threading.Thread(target = Com).start()
if DISPENSER:
  threading.Thread(target = Com2).start()
if BILL_ACCEPTOR:
  threading.Thread(target = Money).start()
threading.Thread(target = phone_receive).start()
threading.Thread(target = send).start()
