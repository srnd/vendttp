#!/usr/bin/env python

import sys, socket, string, threading

HOST="localhost"
PORT=8637

#HOST="irc.rizon.net"
#PORT=6667

s = socket.socket()
s.connect((HOST,PORT))

print "Money Client Connected"

RUNNING = True

def send(s):
  global RUNNING
  while RUNNING:
    message = raw_input()
    if len(message) != 0:
      s.send(message)

def receive(s):
  global RUNNING, sendThread
  while RUNNING:
    message = s.recv(500).rstrip()
    if message == "kick":
      RUNNING = False
      s.close()
      sendThread._Thread__stop()
      print("kicked")
      exit()
    elif len(message) != 0:
      print(message)

sendThread = threading.Thread(target=send, args=(s,))
receiveThread = threading.Thread(target=receive, args=(s,))
sendThread.start()
receiveThread.start()
