#!/usr/bin/env python

import sys, socket, string

HOST="127.0.0.1"
PORT=8636

#HOST="irc.rizon.net"
#PORT=6667

s = socket.socket()
s.connect((HOST,PORT))

while True:
#  try:
  line = s.recv(500).rstrip()
#  except :
  if len(line) == 0:
    exit()

  print(line)
