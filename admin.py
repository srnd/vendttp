#!/usr/bin/env python2.7

import sqlite3, sys

conn = sqlite3.connect('items.sqlite')
c = conn.cursor()
conn.commit()

print "Execute 'help' for a list of commands"

while True:
  sys.stdout.write("? ")
  command = raw_input()
  if command == "exit" or command == "quit" or command == "q":
    conn.commit()
    c.close()
    break
  elif command == "help":
    print """Commands:
  exit: exits"""
