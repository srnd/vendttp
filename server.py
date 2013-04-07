#!/usr/bin/env python2.7

import sys, socket, string, threading, urllib, json, time, serial, random, hashlib, math, re

RUNNING = True
HOST="192.168.15.24"
PORT=8636
PORT2=8637

def Send(t, c, cs):
  global RUNNING
  while RUNNING:
    message = raw_input()
    cs.send(message)

def Recv(cs):
  global RUNNING, username
  while RUNNING:
    try:
      stuff = cs.recv(500).rstrip()
      if len(stuff) != 0:
        if stuff == "logout":
          username = ""
        print stuff
    except:
      print "Disconnecting"
      if t:
        t._Thread__stop()
      if c:
        c._Thread__stop()
      RUNNING = False
      return

def Com(ser, cs):
  global username
  ser.setDTR(False)
  while RUNNING:
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

    url = "http://my.studentrnd.org/api/balance?application_id=APP_ID_GOES_HERE"

    url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

    sig = hashlib.sha256(str(curtime) + str(rand) + "PRIVATE_KEY_GOES_HERE").hexdigest()

    url += sig

    balance = json.loads(urllib.urlopen(url).read())['balance']

    response = "<response type=\"account\"><account name=\"" + username.replace(".", " ") + "\" balance=\"" + str(balance) + "\" /></response>"

    try:
      cs.send(response)
      print "Logged in: " + username
      time.sleep(2)
    except:
      pass

def Money(ms, cs):
  global RUNNING, username
  while RUNNING:
    try:
      message = ms.recv(500).rstrip()
    except:
      print "Shutting down"
      RUNNING = False
      return

    pmessage = re.search(r'^insert (?P<amount>\d+)$', message)
    if pmessage:
      if username != "":
        curtime = str(int(time.time()))
        rand = random.randint(0, math.pow(2, 32) - 1)

        url = "http://my.studentrnd.org/api/balance/eft?application_id=APP_ID_GOES_HERE"

        url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

        sig = hashlib.sha256(str(curtime) + str(rand) + "PRIVATE_KEY_GOES_HERE").hexdigest()

        url += sig

        data = {'username': username, 'amount': pmessage.group('amount'), 'description': "Vending machine deposit", 'type': 'deposit'}

        nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

        print "Deposited " + pmessage.group('amount') + " dollars into " + username + "'s account. New balance: " + nbalance

        cs.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>")
      else: 
        cs.send("return")


username = ""

ser = None
for i in range(1, 10):
  try:
    ser = serial.Serial(port = '/dev/com' + str(i), baudrate = 2400, parity = serial.PARITY_NONE, stopbits = 1,
bytesize = 8)
    break
  except:
    continue

if ser == None:
  print "No RFID scanner detected. Exiting..."
  exit()

s = socket.socket()
s.bind((HOST,PORT))
s.listen(5)

s2 = socket.socket()
s2.bind((HOST,PORT2))
s2.listen(5)


print "Starting server. Waiting for money client"

cs2, address = s2.accept()

print("Money server connection from ", address)


cs, address = s.accept()

print("Connection from ", address)

RUNNING = True

c = threading.Thread(target = Com, args=(ser, cs))
t = threading.Thread(target = Recv, args=(cs, ))
c.start()
t.start()
threading.Thread(target = Send, args=(t, c, cs)).start()
threading.Thread(target = Money, args=(cs2,cs)).run()
