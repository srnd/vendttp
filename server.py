#!/usr/bin/env python2.7

import sys, socket, string, threading, urllib, json, time, serial, random, hashlib, math, re, sqlite3

RUNNING = True
HOST="localhost"
PORT=8636
HOST2="localhost"
PORT2=8637

def Send(t, c, cs):
  global RUNNING
  while RUNNING:
    message = raw_input()
    cs.send(message)

def Recv(cs, ms):
  global RUNNING, username, itemqueue
  while RUNNING:
    try:
      stuff = cs.recv(500).rstrip()
      if len(stuff) != 0:
        pstuff = re.search("^i(?P<id>\d\d)$", stuff)
        if stuff == "logout":
          username = ""
          ms.send("disable")
        elif pstuff and username != "":
          itemqueue[len(itemqueue)] = int(pstuff.group("id"))
        print stuff
    except:
      print "Disconnecting"
      if t:
        t._Thread__stop()
      if c:
        c._Thread__stop()
      RUNNING = False
      return

def Com(ser, cs, ms):
  global username, RUNNING
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

    response = "<response type=\"account\"><account name=\"" + username.replace(".", " ") + "\" balance=\"" + str(balance) + "\" /></response>\r\n"

    conn = sqlite3.connect('items.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
               (id integer primary key, vendId numeric, price numeric, quantity numeric, name text, category text)''')
    conn.commit()

    items = {}
    for item in c.execute("SELECT * from items ORDER BY id"):
      if item[5] in items:
        items[item[5]] += "<item id=\"" + str(item[0]) + "\" vendId=\"" + str(item[1]) + "\" price=\"" + str(item[2]) + "\" quantity=\"" + str(item[3]) + "\" name=\"" + item[4] + "\" />"
      else:
        items[item[5]] = "<item id=\"" + str(item[0]) + "\" vendId=\"" + str(item[1]) + "\" price=\"" + str(item[2]) + "\" quantity=\"" + str(item[3]) + "\" name=\"" + item[4] + "\" />"

    conn.close()

    response2 = "<response type=\"inventory\">"
    for category, item in items.iteritems():
      response2 += "<category name=\"" + category + "\">" + item + "</category>"
    response2 += "</response>\r\n"

    try:
      cs.send(response)
      cs.send(response2)
      print "Logged in: " + username
      ms.send("enable")
      time.sleep(2)
    except:
      RUNNING = False
      return

def Com2(ser, cs):
  global itemqueue
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

        cs.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")

        ser.write("i" + str(i))
        
        c.execute("UPDATE items SET quantity = ? WHERE vendId = ? LIMIT 1", item[3] - 1, i)
        conn.commit()

      conn.close()
  

def Money(ms, cs):
  global RUNNING, username

  while RUNNING:
    try:
      message = ms.recv(500).rstrip()
    except:
      print "Shutting down"
      RUNNING = False
      return

    try:
      amount = int(message) # this is really the line we're worried about with the try/catch
    except ValueError:
      print "From Money Client: " + message
      continue
    if username != "":
      curtime = str(int(time.time()))
      rand = random.randint(0, math.pow(2, 32) - 1)

      url = "http://my.studentrnd.org/api/balance/eft?application_id=APP_ID_GOES_HERE"

      url += "&time=" + curtime + "&nonce=" + str(rand) + "&username=" + username + "&signature="

      sig = hashlib.sha256(str(curtime) + str(rand) + "PRIVATE_KEY_GOES_HERE").hexdigest()

      url += sig

      data = {'username': username, 'amount': message, 'description': "[Test] Vending machine deposit", 'type': 'deposit'}

      nbalance = str(json.loads(urllib.urlopen(url, urllib.urlencode(data)).read())['balance'])

      print "Deposited $" + message + " into " + username + "'s account. New balance: $" + nbalance

      cs.send("<response type=\"balanceUpdate\"><balance>" + nbalance + "</balance></response>\r\n")
    else:
      print message + " dollars inserted; ejected"
      cs2.send("return")


username = ""

ser = None
sernum = 0
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

ser2 = None
for i in range(sernum, 10):
  try:
    ser2 = serial.Serial(i)
    break
  except:
    continue

if ser2 == None:
  print "Can't connect to vending machine. Exiting..."
  exit()


s = socket.socket()
s.bind((HOST,PORT))
s.listen(5)

s2 = socket.socket()
s2.bind((HOST2,PORT2))
s2.listen(5)


print "Starting server. Waiting for money client"

ms, address = s2.accept()

print "Money Client connection from ", address


cs, address = s.accept()

print "Phone Client Connection from ", address

RUNNING = True

c = threading.Thread(target = Com, args=(ser, cs, ms))
t = threading.Thread(target = Recv, args=(cs, ms))
c.start()
t.start()
threading.Thread(target = Send, args=(t, c, cs)).start()
threading.Thread(target = Com2, args=(ser2, cs)).start()
threading.Thread(target = Money, args=(ms, cs)).run()
