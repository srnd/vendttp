#!/usr/bin/env python2.7

try: from settings import EMULATE
except: EMULATE = False
try: from settings import DEBUG
except: DEBUG = False

import sys, socket, string, threading, urllib, json, \
       time, random, hashlib, math, re, sqlite3
import serial
#if EMULATE:
#  import emulate
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
         username, itemqueue
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
      pstuff = re.search("^i(?P<id>\d\d)$", stuff)
      if message == "logout":
        username = ""
        try:
          money_sock.send("disable")
        except:
          print "[ERROR] failed to communicate with bill acceptor"
      elif pstuff and username != "":
        itemqueue[len(itemqueue)] = int(pstuff.group("id"))
      print message
    #if program is here, phone client has disconnected
    print "Phone client disconnected"
    phone_sock = None

def Com():
  global phone_sock, money_sock, ser, username
  for i in range(1, 10):
    try:
      ser = serial.Serial(i)
      ser.baudrate = 2400
      sernum = i
      break
    except:
      continue

  if ser == None:
    print "No RFID scanner detected. Exiting..."
    exit()
  # TODO: fix this so it waits for the connection
  
  ser.setDTR(False)
  while True:
    ser.flushInput()
    ser.setDTR(True)
    stri = ""
    i = 'G'
    while i != '\r':
      i = ser.read()
      if i != '\n' and i != '\r':
        stri = stri + i
    ser.setDTR(False)

    curtime = str(int(time.time()))
    rand = random.randint(0, math.pow(2, 32) - 1)
    username = json.loads(urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + stri).read())['username']

    url  = "http://my.studentrnd.org/api/balance?application_id=APP_ID_GOES_HERE"
    url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username
    url += "&signature=" + hashlib.sha256(str(curtime) + str(rand) + \
                                          "PRIVATE_KEY_GOES_HERE").hexdigest()

    balance = json.loads(urllib.urlopen(url).read())['balance']

    response = E('response',
                 type = 'asdf')
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
      if item[5] in items:
        items[item[5]].append(E('item',
                                id = str(item[0]),
                                vendId = str(item[1]),
                                price = str(item[2]),
                                quantity = str(item[3]),
                                name = item[4]))
      else:
        items[item[5]] = [E('item',
                            id = str(item[0]),
                            vendId = str(item[1]),
                            price = str(item[2]),
                            quantity = str(item[3]),
                            name = item[4])]

    conn.close()

    response2 = E('response', type='inventory')
    for category, items in items.iteritems():
      response2 = E('category', name=category)
      for item in items:
        response2.append(item)

    try:
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
    time.sleep(2)

#TODO:  REFACTOR
def Com2():
  global ser, phone_sock, itemqueue
  while True:
    if len(itemqueue) != 0:
      conn = sqlite3.connect('items.sqlite')
      c = conn.cursor()
      conn.commit()

      for i in itemqueue:
        c.execute("SELECT * from items where vendId = ? LIMIT 1", i)

        item = c.fetchone()
        
        curtime = str(int(time.time()))
        rand = random.randint(0, math.pow(2, 32) - 1)

        url = "http://my.studentrnd.org/api/balance/eft?application_id=APP_ID_GOES_HERE"

        url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

        sig = hashlib.sha256(str(curtime) + str(rand) + "PRIVATE_KEY_GOES_HERE").hexdigest()

        url += sig

        data = {'username': username, 'amount': str(item[2]), 'description': "[Test] Vending machine purchase: " + item[4], 'type': 'withdrawl'}

        nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

        phone_sock.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")

        ser.write("i" + str(i))
        
        c.execute("UPDATE items SET quantity = ? WHERE vendId = ? LIMIT 1", item[3] - 1, i)
        conn.commit()

      conn.close()
  

def Money():
  global phone_sock, money_listener, money_sock, username

  while True:
    money_sock, address = money_listener.accept()
    print "Money client connection from ", address
    while True:
      try:
        message = money_sock.recv(500).rstrip()
        if len(message) == 0:
          break
      except:
        break
      try:
        amount = int(message)
      except ValueError:
        print "Anomolous message from money client: " + message
        continue
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
          phone_sock.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")
        except:
          print "[ERROR] failed to communicate with phone"
        
      else:
        print message + " dollars inserted; ejecting"
        try:
          money_sock.send("return")
          money_sock.send("disable")
        except:
          print "[ERROR] failed to communicate with bill acceptor"
    #if the program is here, money client has disconnected
    print "Money client disconnected"
    money_sock = None

print "Starting server. Waiting for clients"

if not DEBUG:
  # to move
  for i in range(sernum, 10):
    try:
      ser2 = serial.Serial(i)
      break
    except:
      continue

  if ser2 == None:
    print "Can't connect to vending machine. Exiting..."
    exit()
  #/to move
  threading.Thread(target = Com).start()
  threading.Thread(target = Com2).start()
threading.Thread(target = phone_receive).start()
threading.Thread(target = send).start()
threading.Thread(target = Money).start()
