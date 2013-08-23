#!/usr/bin/env python2.7
import os, sqlite3, sys, time
from collections import OrderedDict
from types import FunctionType

#columns defines the columns in the sqlite database. It's written like this for
#ease of definition, then compiled into other forms for ease of use.

#columns = [([db name], [print name], [extra names], [padding], [formatting]),
#           ...
#          ]
columns = [("vendId",   None,  ['id'],  0,  "%02d"),
	   ("price",    None,  [],      1,  "%.02f"),
	   ("quantity", "qty", ['qty'], 1,  "%02d"),
           ("name",     None,  [],      16, "%s"),
           ("category", None,  [],      10, "%s")]

#conversion
ordered = OrderedDict()
column_aliases = {}
for column in columns:
  ordered[column[0]] = {"printed" : column[1] or column[0],
                        "padding" : column[3],
                        "format"  : column[4]}
  for alias in column[2]:
    column_aliases[alias] = column[0]
columns = ordered

def validate_vendId(vendId):
  if vendId.isdigit() and len(vendId) <= 2:
    return vendId.zfill(2)
  else:
    return None

def validate_price(price):
  try:
    return float(price.strip("$"))
  except ValueError:
    return None

def validate_quantity(quantity):
  try:
    return int(quantity)
  except ValueError:
    return None

validate_name = lambda x: x if x else None
validate_cat = validate_name

validate = {'vendId'   : validate_vendId,
            'price'    : validate_price,
            'quantity' : validate_quantity,
            'name'     : validate_name,
            'category' : validate_cat}

def gen_key():
  key = int(time.time()%1e8*10)
  c.execute("INSERT OR REPLACE INTO globals VALUES (?,?)", ["dbkey", key])

def commit():
  gen_key()
  conn.commit()

def printQuery(query):  
  for name, attrs in columns.iteritems():
    sys.stdout.write(name)
    sys.stdout.write(" " * (attrs['padding'] + 1))
  sys.stdout.write("\n")

  for name, attrs in columns.iteritems():
    sys.stdout.write("-" * (len(name) + attrs['padding'] ))
    sys.stdout.write(" ")
  sys.stdout.write("\n")
  
  for item in query:
    for i, (column, attrs) in enumerate(columns.iteritems()):
      try:
        text = attrs['format'] % (item[i])
      except TypeError:
        try:
          text = attrs['format'] % float(item[i])
        except:
          text = "None"
      maxlen = len(column) + attrs['padding'] + 1
      if len(text) > maxlen:
        text = text[:maxlen - 3] + "..."
      else:
        text = text.ljust(maxlen)
      sys.stdout.write(text)
    sys.stdout.write("\n")

def removeItem(vendId):
  c.execute("DELETE FROM items WHERE vendId = ?", [vendId])
  commit()

def addItem(vendId, price, quantity, name, category):
  removeItem(vendId)
  c.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", [vendId, price, quantity, name, category])
  commit()

#evaluate
def getCol(vendId, column):
  if not column in ("price", "quantity", "name", "category"):
    return
  c.execute("SELECT " + column + " FROM items WHERE vendId = ?", [vendId])
  col = c.fetchone()
  if col != None:
    col = list(col)
    if len(col) == 1:
      return col[0]
  return col

# command system setup

commands = {}
aliases = {}

def expand_cmd(short):
  candidates = map(lambda a: aliases[a], filter(lambda a: a.startswith(short), aliases))
  candidates += filter(lambda c: c.startswith(short), commands)
  candidates = set(candidates)
  if len(candidates) == 1:
    return candidates.pop()
  elif len(candidates) > 1:
    for candidate in candidates:
      if candidate == short:
        return candidate
    raise ExpansionError("%s is not a valid short-from command name" % short)
  else:
    raise ExpansionError("%s is not a valid command name" % short)

def expand_col(short):
  candidates = map(lambda a: column_aliases[a], filter(lambda a: a.startswith(short), column_aliases))
  candidates += filter(lambda c: c.startswith(short), columns)
  candidates = set(candidates)
  if len(candidates) == 1:
    return candidates.pop()
  elif len(candidates) > 1:
    raise ExpansionError("%s is not a valid short-from column name" % short)
  else:
    raise ExpansionError("%s is not a valid column name" % short)

class BadArgsException(Exception): pass
class ExpansionError(BadArgsException): pass
class BadArgstringException(Exception): pass

def cmd(name, *_aliases):
  def decorator(function):
    commands[name] = function
    return function
  if type(name) == FunctionType:
    function = name
    name = function.__name__
    return decorator(function)
  if _aliases:
    for alias in _aliases:
      aliases[alias] = name
  return decorator

def run_cmd(input_string):
  split = input_string.split(" ", 1)
  command = split[0]
  pos = command.find('"')
  if pos > -1:
    print "! Could not parse command: unexpected quote at pos %s" % pos
    return
  if len(split) == 2:
    try:
      args = parse(split[1])
    except BadArgstringException as e:
      print "! Could not parse arguments: %s" % e.message
      return
  else:
    args = []
  try:
    command = expand_cmd(command)
  except ExpansionError:
    print "! `%s` is not a command. run `help` for a list of commands" % command
    return
  if command in aliases:
    command = aliases[command]
  try:
    commands[command](args)
  except BadArgsException as e:
    print "! Invalid argument(s): " + e.message
    return
  except Abort:
    return

def parse(string):
  args = []
  i = 0
  while True: # do while
    if i == len(string): return args
    if string[i] != " ": break
    i += 1
  j = 0
  quote = string[i] == '"'
  while i+j < len(string):
    j += 1
    if quote:
      if i+j == len(string):
        raise BadArgstringException("expected closing quote, got EOL")
      if string[i+j] == '"':
        if i+j+1 < len(string) and string[i+j+1] != " ":
          raise BadArgstringException("expected space at %s, found %s" % (i+j+1, string[i+j+1]))
        args.append(string[i+1:i+j])
        i += j + 2
        j = 0
        while i < len(string) and string[i] == " ":
          i += 1
        if i < len(string):
          quote = string[i] == '"'
    else:
      if i+j < len(string):
        if string[i+j] == " ":
          args.append(string[i:i+j])
          i += j
          j = 0
          while i < len(string) and string[i] == " ":
            i += 1
          if i < len(string):
            quote = string[i] == '"'
        elif string[i+j] == '"':
          raise BadArgstringException("unexpected quote at pos %s" % (i+j))
      else:
        args.append(string[i:i+j])
  return args

class Abort(Exception): pass
def ask(question, validate, invalid_msg = None):
  if not validate: validate = lambda x: x
  while True:
    ans = raw_input(question)
    if ans == "": raise Abort()
    ans = validate(ans)
    if ans != None: break
    if invalid_msg: print invalid_msg
  return ans

def validate_y_n(string):
  x = string[0].lower()
  if x in ('y','n'):
    return x
  else:
    return

################
#   COMMANDS   #
################

@cmd('help')
def help_cmd(args):
  """Prints help information.
Usages: help
        help [command]"""
  if len(args) == 0:
    print "# The following is a list of commands that this program recognizes."
    print "# Call `help [command]` for more detailed information."
    print "# Note: all command and column names can be shortened as short as you want,"
    print "#       barring conflict with other names"
    maxlen = max(map(len, commands.keys()))
    items = commands.items()
    items.sort(key = lambda x: x[0])
    for command, func in items:
      sys.stdout.write("# " + command.ljust(maxlen) + " : ")
      if func.__doc__:
        doclines = func.__doc__.split("\n")
        sys.stdout.write(doclines[0] + "\n")
      else:
        sys.stdout.write("No Documentation")
  else:
    if len(args) > 1:
      print "~ Warning: `help` takes at most one argument; ignoring all extras."
    command = expand_cmd(args[0])
    if command in aliases:
      print "# %s is an alias for %s." % (command, aliases[command])
      command = aliases[command]
    if command not in commands:
      raise BadArgsException("`%s` is not a command or command-alias." % args[0])
    doc = commands[command].__doc__
    prefix = "%s: " % command
    sys.stdout.write("# " + prefix)
    if doc:
      doclines = doc.split("\n")
      sys.stdout.write(doclines[0] + "\n")
      for line in doclines[1:]:
        print "# " + " " * len(prefix) + line
    else:
      sys.stdout.write("No Documentation")

class Exit(Exception): pass
@cmd('exit', 'quit')
def exit(args):
  """Exits the program.
Usage: exit"""
  global running
  if args:
    raise BadArgsException("`exit` takes no arguments")
  commit()
  c.close()
  running = False
  print "Goodbye"
  raise Exit

@cmd("print")
def printTable(args):
  """Prints the inventory
Usage: print
       print order [column]
       print [column] [value]
       print [vendId]"""
  if not args:
    printQuery(c.execute("SELECT * FROM items ORDER BY vendId"))
  elif len(args) == 1:
    vendId = args[0]
    printQuery(c.execute("SELECT * FROM items WHERE vendId = ?", [vendId]))
  else:
    if len(args) > 2:
      print "~ Warning: `print` takes at most two arguments and ignors all extras."
      print "~ Note: If you want to enter an argument which includes spaces, wrap it in double-quotes."
    if args[0] == "order":
      column = expand_col(args[1])
      printQuery(c.execute("SELECT * FROM items ORDER BY %s" % column))
    else:
      column = expand_col(args[0])
      value = args[1]
      printQuery(c.execute("SELECT * FROM items WHERE %s = ?" % column, [value]))

@cmd("add", "new")
def add(args):
  """Add a new item to the database
Usage: add
       add [vendId]
       add [vendId] ([column] [value] ...)
       add [vendId] [price] [quantity] [name] [category]"""
  
  vendId = None
  price = None
  quantity = None
  name = None
  category = None
  
  # parse args; fill in the above
  if len(args) > 0:
    if validate['vendId'](args[0]) == None:
      raise BadArgsException("%s is not a valid vendId" % args[0])
    vendId = args[0]
    if len(args) == 5 and not args[1].isalpha(): # the two sides of this if/else are WAY too similar and should be compressed
      price = validate['price'](args[1])
      if price == None:
        raise BadArgsException("%s is neither a valid price, nor a valid column" % args[1])
      quantity = validate['quantity'](args[2])
      if quantity == None:
        raise BadArgsException("%s is not a valid quantity" % args[2])
      name = args[3]
      if name == None: raise BadArgsException("name cannot be empty")
      category = args[4]
      if category == None: raise BadArgsException("category cannot be empty")
    else:
      if len(args) % 2 != 1:
        raise BadArgsException("there must be an even number of arguments after vendId")
      pairs = ((args[i], args[i+1]) for i in xrange(1, len(args), 2))
      for column, value in pairs:
        column = expand_col(column)
        if column == "price":
          price = validate['price'](value)
          if price == None:
            raise BadArgsException("%s is not a valid price" % value)
        elif column == "quantity":
          quantity = validate['quantity'](value)
          if quantity == None:
            raise BadArgsException("%s is not a valid quantity" % value)
        elif column == "name":
          name = validate['name'](value)
          if name == None:
            raise BadArgsException("name cannot be empty")
        elif column == "category":
          category = validate['category'](value)
          if category == None:
            raise BadArgsException("category cannot be empty")
  c.execute("SELECT name FROM items WHERE vendId = ?", [vendId])
  result = c.fetchone()
  if result is not None:
    print "! Item \"%s\" already exists at vendId %s" % (result[0], vendId)
    overwrite = ask("? Overwrite with new item (y/n): ",
                    validate_y_n)
    if overwrite != "y":
      print "! Aborting."
      return
  if None in [vendId, price, quantity, name, category]:
    print "# Add item:"
    print "# [enter a blank attribute to abort]"
    try:
      if vendId == None:
        vendId = ask("? vendId: ", validate['vendId'], "! vendId must be two digits.")
      if price == None:
        price = ask("? price: ", validate['price'], "! price must be a dollar/cent amount.")
      if quantity == None:
        quantity = ask("? quantity: ", validate['quantity'], "! quantity must be an integer amount")
      if name == None:
        name = ask("? name: ", validate['name'], "! name cannot be empty.")
      if category == None:
        category = ask("? category: ", validate['category'], "! categroy cannot be empty.")
    except Abort:
      return
  print "# adding item"
  addItem(vendId, price, quantity, name, category)

@cmd("clear", "reset")
def clear(args):
  """Clears the database
Usage: reset"""
  if args:
    raise BadArgsException("`clear` takes no arguments")
  confirm = ask("? Really clear database? [CANNOT BE UNDONE] (y/n): ", validate_y_n)
  if confirm == "y":
    print "# Database cleared"
    c.execute("DELETE FROM items")
    commit()

@cmd("delete")
def delete(args):
  """Removes an item from the database
Usage: delete
       delete [vendId]"""
  if len(args) == 0:
    vendId = raw_input("? vendId: ")
  elif len(args) == 1:
    vendId = args[0]
  vendId = validate['vendId'](vendId)
  if vendId == None:
    print "! vendId must be two digits."
    return
  c.execute("SELECT name FROM items WHERE vendId = ?", [vendId])
  item = c.fetchone()
  if item is not None:
    confirm = ask("? Really delete %s (%02d) from database?(y/n) " % (item[0], int(vendId)), validate_y_n)
    if confirm == "y":
      removeItem(vendId)
      print "# Item removed."
    else:
      print "# Item not removed."
  else:
    print "! No item with that vendId."

@cmd('update')
def update(args = None):
  """Updates an item in the database
Usage: update
       update [vendId]
       update [vendId] [column]
       update [vendId] ([column] [new value] ...)"""
  vendId = None
  column = None
  changes = {}
  # parse args
  if len(args) > 0:
    vendId = validate['vendId'](args[0])
    if vendId == None:
      raise BadArgsException("vendId must be two digits.")
  if len(args) == 2:
    column = expand_col(args[1])
  elif len(args) > 2:
    if len(args) % 2 == 0:
      raise BadArgsException("there must be an even number of arguments after vendId")
    for column, value in ((args[i], args[i+1]) for i in xrange(1, len(args), 2)):
      column = expand_col(column)
      valid_value = validate[column](value)
      if valid_value == None:
        raise BadArgsException("%s is not a valid %s" % (value, column))
      changes[column] = valid_value
    column = None
  # fill in blanks and validate
  if not changes:
    print "# [enter empty string to abort]"
  if not vendId:
    vendId = ask("? vendId: ", validate['vendId'], "! vendId must be two digits.")
  name = getCol(vendId, "name")
  if name == None:
    print "! vendId not found"
    return
  if not changes and not column:
    # I should probably reevaluate this setup
    def validate_col(col):
      try:
        return expand_col(col)
      except ExpansionError as e:
        print "! " + e.message
        return None
    column = ask("? column: ", validate_col)
  if column:
    value = ask("? value: ", validate[column], "! invalid value")
    changes[column] = value
  statement = "UPDATE items SET"
  for column in changes.keys():
    statement += " %s = ?," % column
  statement = statement[:-1] + " WHERE vendId = ?"
  c.execute(statement, changes.values() + [vendId])
  print "# updating item."
  commit()

#############
#  PROGRAM  #
#############


def main():
  global conn, c
  if os.path.exists('items.sqlite') and not os.path.exists('database.sqlite'):
    os.rename('items.sqlite', 'database.sqlite')
  conn = sqlite3.connect('database.sqlite')
  c = conn.cursor()
  c.execute('''CREATE TABLE IF NOT EXISTS globals
               (name TEXT PRIMARY KEY,
                value BLOB)''')
  c.execute('''CREATE TABLE IF NOT EXISTS items
               (vendId INTEGER PRIMARY KEY,
                price REAL,
                quantity INTEGER,
                name TEXT,
                category TEXT)''')
  gen_key()
  conn.commit()
  running = True
  caught = False

  print "# Type 'help' for a list of commands"
  while running:
    try:
      input_string = raw_input("> ")
      if len(input_string) == 0:
        continue
      run_cmd(input_string)
      caught = False
    except KeyboardInterrupt:
      if not caught:
        print "Caught keyboard interrupt. Do it again to exit, use the `exit` command, or use ctrl-D"
        caught = True
      else:
        break
    except EOFError:
      break
    except Exit:
      break

if __name__ == "__main__":
  main()
