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

def getCol(vendId, column = "name"):
  if not column in ("price", "quantity", "name", "category"):
    return
  c.execute("SELECT " + column + " FROM items WHERE vendId = ?", [vendId])
  cols = c.fetchone()
  if cols != None:
    cols = list(cols)
    if len(cols) == 1:
      return cols[0]
  return cols

################
#   COMMANDS   #
################

def exit(args = None):
  """(e)xit
Exits"""
  global running
  print "Goodbye"
  conn.commit()
  c.close()
  running = False

def printTable(args = None):
  """(p)rint
Prints all the items in the inventory"""
  printQuery("SELECT * FROM items ORDER BY vendId")

def help(args = None):
  """(h)elp
Prints help messages
Usage:
  help
  help [command]"""
  if args == None or len(args) == 0:
    print "Commands: "
    for command, description in commands.iteritems():
      sys.stdout.write("  ")
      comtext = description.__doc__.split("\n")[0]
      sys.stdout.write(comtext + ":")
      sys.stdout.write(" " * (10 - len(comtext)))
      sys.stdout.write(description.__doc__.split("\n")[1])
      print
    print "Type help [command] to get detailed help for a command"
  else:
    for command, description in commands.iteritems():
      if args[0] in command:
        for doc in description.__doc__.split("\n")[1:]:
          print doc
        return

    print "Unknown command"

def add(args = None):
  """(a)dd
Add a new item to the database
Usage:
  add
  add [vendId]
  add [column] [value]
  add [vendId] [price] [quantity] [name] [category]"""
  price = None
  quantity = None
  name = None
  category = None
  columns = ("p", "price", "quantity", "q", "name", "n", "category", "c")
  if args == None or len(args) == 0:
    print "Add item:"
    vendId = raw_input("vendId? ")
  elif len(args) == 5:
    addItem(args[0], args[1], args[2], args[3], args[4])
  elif len(args) == 1:
    vendId = args[0]
  elif len(args) == 3:
    vendId = args[0]
    if args[1] in columns:
      if column[0] == "p":
        price = args[2]
      elif column[0] == "q":
        quantity = args[2]
      elif column[0] == "n":
        name = args[2]
      elif column[0] == "c":
        category = args[2]
  else:
    help(["add"])
    return
  c.execute("SELECT name FROM items WHERE vendId = ?", [vendId])
  name = c.fetchone()
  if name is not None:
    print "Selected %s (%02d)" % (name[0], int(vendId))
    overwrite = raw_input("Overwrite with new item?(y/n) ")
    if overwrite[0] == "y":
      addItem(vendId, raw_input("New price? "), raw_input("New quantity? "), raw_input("New name? "), raw_input("New category? "))
  else:
    if price == None:
      price = raw_input("Price? ")
    if quantity == None:
      qauntity = raw_input("Quantity? ")
    if name == None:
      name = raw_input("Name? ")
    if category == None:
      category = raw_input("Category? ")
    addItem(vendId, price, quantity, name, category)

def reset(args = None):
  """(r)eset
Clears the database"""
  confirm = raw_input("Really clear database?(y/n) ")
  if confirm[0] == "y":
    c.execute("DROP TABLE IF EXISTS items")
    c.execute('''CREATE TABLE items
             (vendId integer primary key, price numeric, quantity numeric, name text, category text)''')
    conn.commit()

def delete(args = None):
  """(d)elete
Removes an item from the database
Usage:
  delete
  delete [vendId]"""
  if args == None or len(args) == 0:
    vendId = raw_input("vendId? ")
  elif len(args) == 1:
    vendId = args[0]
  else:
    help(["delete"])
    return
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

def update(args = None):
  """(u)pdate
Updates an item in the database
Usage:
  update
  update [vendId]
  update [vendId] [column]
  update [vendId] [column] [new value]"""

  columnsdoc = """Columns:
  (p)rice
  (q)uantity
  (n)ame
  (c)ategory
"""
  columns = ("p", "price", "quantity", "q", "name", "n", "category", "c")
  if args == None or len(args) > 3:
    help(["update"])
    return
  if len(args) == 0:
    vendId = -1
  else:
    vendId = args[0]
    prompt = False
  name = getCol(vendId, "name")
  while name is None:
    prompt = True
    vendId = raw_input("vendId? ")
    name = getCol(vendId, "name")

  if prompt:
    print "Selected item %s" % name

  if len(args) > 1:
    column = args[1]
  else:
    column = ""
  while not column in columns:
    if column != "":
      print "Invalid column"
    print columnsdoc
    column = raw_input("Column? ")
  if column == "p":
    column = "price"
  elif column == "q":
    column = "quantity"
  elif column == "n":
    column = "name"
  elif column == "c":
    column = "category"

  if len(args) > 2:
    value = args[2]
  else:
    sys.stdout.write("Current value: ")
    if column == "price":
      print "$%.02f" % getCol(vendId, "price")
    else:
      print getCol(vendId, column)
    
    while True:
      value = raw_input("New %s? " % column)
      try:
        if column == "price":
          value = float(value)
        elif column == "quantity":
          value = int(value)
        break
      except ValueError:
        print "Invalid value"
        continue

  c.execute("UPDATE items SET " + column + " = ? WHERE vendId = ?", [value, vendId])
  conn.commit()

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
            ("d", "delete"):              delete,
            ("u", "update"):              update}

while running:
  try:
    command = raw_input("? ")
    command = command.split(" ")
    if len(command) < 1:
      continue
    ran = False
    for com, function in commands.iteritems():
      if command[0] in com:
        try:
          function(command[1:])
          ran = True
        except KeyboardInterrupt:
          print
        break
    if not ran:
      print "Unknown command"
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
    
