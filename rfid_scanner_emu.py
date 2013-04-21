#!/usr/bin/env python

import time, socket

HOST="localhost"
PORT=8638

sock = None

print "RFID Scanner Emulator for VendorTron 2000 server"
while True:
  if sock:
    message = raw_input()
    try:
      sock.send(message)
    except socket.error:
      print "[ERROR] not connected to a server"
      sock = None
  else:
    while True:
      try:
        print "Trying to connect to server"
        if not sock: sock = socket.socket()
        sock.connect((HOST,PORT))
        print "Successfully connected to server"
        break
      except socket.error:
        time.sleep(4)
