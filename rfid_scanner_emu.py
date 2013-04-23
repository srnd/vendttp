#!/usr/bin/env python

import time, socket

HOST="localhost"
PORT=8638

sock = None

print "RFID Scanner Emulator for VendorTron 2000 server"
while True:
  message = None
  if sock:
    message = raw_input()
    try:
      sock.send(message)
      message = None
    except socket.error:
      print "[ERROR] not connected to a server"
      sock = None
  else:
    print "Trying to connect to server"
    while True:
      try:
        if not sock: sock = socket.socket()
        sock.connect((HOST,PORT))
        print "Successfully connected to server"
        if message:
          sock.send(message)
          message = None
        break
      except socket.error:
        time.sleep(4)
