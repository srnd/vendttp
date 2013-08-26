#!/usr/bin/env python2.7
import os, sys
from collections import OrderedDict
from types import FunctionType
import database

####################
#  UTIL AND SETUP  #
####################

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

def printItem(item):
  if item:
    printQuery((item,))
  else:
    printQuery(())

def printQuery(iterator):  
  for name, attrs in columns.iteritems():
    sys.stdout.write(name)
    sys.stdout.write(" " * (attrs['padding'] + 1))
  sys.stdout.write("\n")

  for name, attrs in columns.iteritems():
    sys.stdout.write("-" * (len(name) + attrs['padding'] ))
    sys.stdout.write(" ")
  sys.stdout.write("\n")
  
  for item in iterator:
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

##########################
#  COMMAND SYSTEM SETUP  #
##########################

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
    raise ExpansionError("%s is not a valid short-form command name" % short)
  else:
    raise ExpansionError("%s is not a valid command name" % short)

def expand_col(short):
  candidates = map(lambda a: column_aliases[a], filter(lambda a: a.startswith(short), column_aliases))
  candidates += filter(lambda c: c.startswith(short), columns)
  candidates = set(candidates)
  if len(candidates) == 1:
    return candidates.pop()
  elif len(candidates) > 1:
    raise ExpansionError("%s is not a specific enough short-form column name" % short, True)
  else:
    raise ExpansionError("%s is not a valid column name" % short, True)

class BadArgsException(Exception):
  def __init__(self, message, show_quotes_hint):
    Exception.__init__(self, message)
    self.show_quotes_hint = show_quotes_hint
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
    if e.show_quotes_hint:
      print "~ Note: If you want to enter an argument which includes spaces, wrap it in double-quotes."
    return
  except Abort:
    return

def parse(string):
  args = []
  i = 0
  while True:
    if i == len(string): return args
    if string[i] != " ": break
    i += 1
  j = 0
  quote = '"' == string[i]
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
  running = False
  print "Goodbye"
  raise Exit

@cmd("print")
def printTable(args):
  """Prints the inventory
Usage: print (order [column])                 # print all items (ordered by [column])
       print [column] [value] (order [colum]) # print items where [column] is [value]
       print [vendId]                         # print specific item"""
  if not args:
    printQuery(database.get_items_generator())
  elif len(args) == 1:
    vendId = args[0]
    printItem(database.get_item(vendId))
  else:
    if len(args) > 4 or len(args) == 3:
      raise BadArgsException("Invalid number of argument tokens", True)
    where = None
    order_by = None
    if args[-2] == "order":
      column = expand_col(args[-1])
      order_by = column
      args = args[:-2]
    elif len(args) == 4: raise BadArgsException("Error parsing argument token #3", True)
    if len(args) == 2:
      column = expand_col(args[0])
      value = args[1]
      printQuery(database.get_items_generator(where = (column, value),
                                              order_by = order_by))
    else:
      printQuery(database.get_items_generator(order_by = order_by))

@cmd("add", "new")
def add(args):
  """Add a new item to the database
Usage: add
       add [vendId]
       add [vendId] [price] [quantity] [name] [category]
       add [vendId] {[column] [value] ...}"""
  
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
    # the code comprised by this if/else can certainly be improved
    if len(args) == 5 and not args[1].isalpha():
      price = validate['price'](args[1])
      if price == None:
        raise BadArgsException("argument token #2 (%s) is neither a valid price, nor a valid column" % args[1])
      quantity = validate['quantity'](args[2])
      if quantity == None:
        raise BadArgsException("%s is not a valid quantity" % args[2])
      name = args[3]
      if name == None: raise BadArgsException("name cannot be empty")
      category = args[4]
      if category == None: raise BadArgsException("category cannot be empty")
    else:
      if len(args) % 2 != 1:
        raise BadArgsException("invalid number of argument tokens", True)
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
  if database.item_exists(vendId):
    name = database.get_item_name(vendId)
    print "! Item \"%s\" already exists at vendId %s" % (name, vendId)
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
  database.new_item(vendId, price, quantity, name, category)

@cmd("clear", "reset")
def clear(args):
  """Clears the database
Usage: reset"""
  if args:
    raise BadArgsException("`clear` takes no arguments")
  confirm = ask("? Really clear database? [CANNOT BE UNDONE] (y/n): ", validate_y_n)
  if confirm == "y":
    print "# Database cleared"
    database.clear_items()

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
  #[know nothin in life| but the best shit]
  #[ go  quote  me boy |cause i  said shit]
  if database.item_exists(vendId):
    name = database.get_item_name(vendId)
    confirm = ask("? Really delete %s (%02d) from database?(y/n) " % (name, int(vendId)), validate_y_n)
    if confirm == "y":
      database.delete_item(vendId)
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
      raise BadArgsException("invalid number of argument tokens", True)
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
  name = database.get_item_name(vendId)
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
  database.update_item(vendId, **changes)
  print "# item updated."

##################
#  PROGRAM MAIN  #
##################

def main():
  database.connect()
  
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
