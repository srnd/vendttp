#!/usr/bin/env python

import time, socket, threading

HOST="localhost"
PORT=8638

sock = None

def send():
  global sock
  while True:
    message = raw_input()
    if sock:
      try:
        sock.send(message)
      except:
        print "[ERROR] not connected to a server"
        sock = None
    else:
      print "[ERROR] not connected to a server"
      while sock == None:
        time.sleep(4)

def receive():
  global sock
  while True:
    try:
      sock = socket.socket()
      sock.connect((HOST,PORT))
      print "Successfully connected to server"
    except:
      time.sleep(4)
      continue
    while sock:
      try:
        message = sock.recv(500).rstrip()
        if len(message) == 0:
          break
      except:
        break
    print "Disconnected from server"

print "RFID scanner emulator for VendorTron 2000 server"

threading.Thread(target=send).start()
threading.Thread(target=receive).start()
