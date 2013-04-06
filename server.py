#!/usr/bin/env python2.7

import sys, socket, string, threading, serial, urllib, json, time

RUNNING = True
HOST="192.168.15.24"
PORT=8636

def Send(s):
  global RUNNING
  while RUNNING:
    message = raw_input()
    if message == "exit":
      s.send("exit\r\n")
      RUNNING = False
      return
    s.send(message)

def Recv(s, t):
  global RUNNING
  while RUNNING:
    try:
      stuff = s.recv(500).rstrip()
      if stuff == "exit":
        RUNNING = False
        t._Thread__stop()
        return
      elif len(stuff) != 0:
        print stuff
    except:
      print "Disconnecting"
      RUNNING = False
      return

def Com(ser, s):
  while True:
    ser.setDTR(False)
    ser.flushInput()
    ser.setDTR(True)
    str = ""
    i = 'G'
    while i != '\r':
      i = ser.read()
      if i != '\n' and i != '\r':
        str = str + i
    ser.setDTR(False)
    ser.flushInput()
    s.send("<response type=\"account\"><account id=\"" + str + "\" name=\"" + json.loads(urllib.urlopen("http://my.studentrnd.org/api/user/rfid?rfid=" + str).read())['username'] + "\" /></response>")
    time.sleep(2)


s = socket.socket()
s.bind((HOST,PORT))
s.listen(5)

ser = None
for i in range(1, 10):
  try:
    ser = serial.Serial(port = '/dev/com' + str(i), baudrate = 2400, parity = serial.PARITY_NONE, stopbits = 1,
bytesize = 8)
    break
  except:
    continue

if ser == None:
  print "No RFID scanner detected. Exitting..."
  exit()

while True:
  cs, address = s.accept()

  print("Connection from ", address)

  RUNNING = True

  t = threading.Thread(target = Send, args=(cs,)).start()
  threading.Thread(target = Recv, args=(cs,t)).start()
  threading.Thread(target = Com, args=(ser,cs)).start()

#while True:
#  cs.send(raw_input() + "\r\n")
#  print cs.recv(500).rstrip()
