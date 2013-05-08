#!/usr/bin/env python2.7

import sqlite3, sys, math

def printQuery(query):  
  columns = [("vendId", 0, "%02d"), ("price", 1, "%.02f"), ("qty", 1, "%02d"), ("name", 12, "%s"), ("category", 4, "%s")]

  for column in columns:
    sys.stdout.write(column[0])
    sys.stdout.write(" " * (column[1] + 1))
  print

  for column in columns:
    sys.stdout.write("-" * (len(column[0]) + column[1] ))
    sys.stdout.write(" ")
  print

  for item in c.execute(query):
    for i, column in enumerate(columns):
      try:
        text = column[2] % (item[i])
      except TypeError:
        text = column[2] % float(item[i])
      if len(text) > len(column[0]) + column[1]:
        text = text[:len(column[0]) + column[1] - 3] + "..."
      sys.stdout.write(text)
      sys.stdout.write(" " * (len(column[0]) + column[1] + 1 - len(text)))

    print

def removeItem(vendId):
  c.execute("DELETE FROM items WHERE vendId = ?", [vendId])
  conn.commit()

def addItem(vendId, price, quantity, name, category):
  removeItem(vendId)
  c.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", [vendId, price, quantity, name, category])
  conn.commit()


################
#   COMMANDS   #
################

def exit():
  """Exits"""
  global running
  print "Goodbye"
  conn.commit()
  c.close()
  running = False

def printTable():
  """Prints all the items in the inventory"""
  printQuery("SELECT * FROM items ORDER BY vendId")

def help():
  """Prints this help message"""
  print "Commands: "
  for command, description in commands.iteritems():
    sys.stdout.write("  ")
    comtext = "%s(%s)" % (command[1], command[0])
    sys.stdout.write(comtext + ":")
    sys.stdout.write(" " * (10 - len(comtext)))
    sys.stdout.write(description.__doc__)
    print

def add():
  """Add a new item to the database"""
  print "Add item:"
  vendId = raw_input("vendId? ")
  c.execute("SELECT name FROM items WHERE vendId = ?", [vendId])
  name = c.fetchone()
  if name is not None:
    print "Selected %s(%02d)" % (name[0], int(vendId))
    overwrite = raw_input("Overwrite with new item?(y/n) ")
    if overwrite[0] == "y":
      addItem(vendId, raw_input("New price? "), raw_input("New quantity? "), raw_input("New name? "), raw_input("New category? "))
  else:
    addItem(vendId, raw_input("Price? "), raw_input("Quantity? "), raw_input("Name? "), raw_input("Category? "))

def reset():
  """Clears the database"""
  confirm = raw_input("Really clear database?(y/n) ")
  if confirm[0] == "y":
    c.execute("DROP TABLE IF EXISTS items")
    c.execute('''CREATE TABLE items
             (vendId integer primary key, price numeric, quantity numeric, name text, category text)''')
    conn.commit()

def delete():
  """Removes an item from the database"""
  vendId = raw_input("vendId? ")
  c.execute("SELECT name FROM items WHERE vendId = ?", [vendId])
  name = c.fetchone()
  if name is not None:
    confirm = raw_input("Really delete %s(%02d) from database?(y/n) " % (name[0], int(vendId)))
    if confirm[0] == "y":
      removeItem(vendId)
      print "Item removed"
    else:
      print "Item not removed"
  else:
    print "No item with that vendId"


#############
#  PROGRAM  #
#############

conn = sqlite3.connect('items.sqlite')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS items
           (vendId integer primary key, price numeric, quantity numeric, name text, category text)''')
conn.commit()
running = True
caught = False

print "Type 'help' for a list of commands"

commands = {("p", "print"):               printTable,
            ("e", "exit", "quit", "q"):   exit,
            ("h", "help", "?"):           help,
            ("a", "add", "new", "n"):     add,
            ("r", "reset", "clear", "c"): reset,
            ("d", "delete"):              delete}

while running:
  try:
    command = raw_input("? ")
    for com, function in commands.iteritems():
      if command in com:
        try:
          function()
        except KeyboardInterrupt:
          print
        break
    caught = False
  except KeyboardInterrupt:
    print
    if not caught:
      print "Caught keyboard interrupt. Do it again to exit, use the exit command, or use ctrl-D"
      caught = True
    else:
      exit()
  except EOFError:
    exit()
    
