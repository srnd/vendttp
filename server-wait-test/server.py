#!/usr/bin/env python2.7

import sys, socket, threading

HOST="localhost"
PORT=8636
HOST2="localhost"
PORT2=8637

client_listener = socket.socket()
client_listener.bind((HOST, PORT))
client_listener.listen(1)
client_socket = None
client_listener2 = socket.socket()
client_listener2.bind((HOST2, PORT2))
client_listener2.listen(1)
client_socket2 = None

def Send():
  global client_socket, client_socket2 
  while True:
    message = raw_input()
    error = False
    try:
      client_socket.send(message)
    except:
      error = True
    try:
      client_socket2.send(message)
    except:
      if error:
        print "[ERROR] cannot send, no client connected"

def Receive1():
  global client_listener, client_socket
  while True:
    client_socket, address = client_listener.accept()
    print "Client #1 connected from ", address
    while True:
      try:
        message = client_socket.recv(500).rstrip()
        if len(message) != 0:
          print "from 1: " + message
        else:
          break
      except socket.error:
        break
    print "Client #1 disconnected"
    client_socket = None

def Receive2():
  global client_listener2, client_socket2
  while True:
    client_socket2, address = client_listener2.accept()
    print "Client #2 connected from ", address
    while True:
      try:
        message = client_socket2.recv(512).rstrip()
        if len(message) != 0:
          print "from 2: " + message
        else:
          break
      except:
        break
    print "Client #2 disconnected"
    client_socket2 = None

print "Starting test server. Waiting for clients."

threading.Thread(target = Send).start()
threading.Thread(target = Receive1).start()
threading.Thread(target = Receive2).start()
