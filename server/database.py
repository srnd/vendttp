import os, time, sqlite3

#### Module Level Globals ####
conn = None
cur = None

columns = ["vendId", "price", "quantity", "name",
           "category"]

#### Utility Stuff ####

class NotConnectedException(Exception): pass
class BadColumnError(Exception): pass

class DummyCursor:
  def execute(self, *args, **kwargs):
    raise NotConnectedException()
cur = DummyCursor()

#### Database Interaction Functions ####

# Connect to the database file
def connect():
  global conn, cur
  if os.path.exists('items.sqlite') and not os.path.exists('database.sqlite'):
    os.rename('items.sqlite', 'database.sqlite')
  conn = sqlite3.connect('database.sqlite', check_same_thread = False)
  cur = conn.cursor()
  cur.execute('''CREATE TABLE IF NOT EXISTS globals
                 (key TEXT PRIMARY KEY,
                  value BLOB)''')
  cur.execute('''CREATE TABLE IF NOT EXISTS items
                 (vendId INTEGER PRIMARY KEY,
                  price REAL,
                  quantity INTEGER,
                  name TEXT,
                  category TEXT)''')
  cur.execute('''CREATE TABLE IF NOT EXISTS depths
                 (vendId INTEGER PRIMARY KEY,
                  depth INTEGER)''')
  conn.commit()

def disconnect():
  if conn:
    conn.close()


## database key

def get_db_key():
  """returns the database key, or None if no database key is found"""
  cur.execute("SELECT value FROM globals WHERE key == 'dbkey'")
  db_key = cur.fetchone()
  if db_key: db_key = db_key[0]
  return db_key

def update_key():
  key = int(time.time()%1e8*10)
  cur.execute("INSERT OR REPLACE INTO globals VALUES ('dbkey', ?)", (key,))


## items

def _get_items(where, order_by):
  query = "SELECT * from items"
  values = []
  if where:
    query += " WHERE %s = ?" % where[0]
    values = where[1:]
  if order_by:
    query += " ORDER BY %s" % order_by
  cur.execute(query, values)

def get_items(where = None, order_by = None):
  _get_items(where, order_by)
  return cur.fetchall()

def get_items_generator(where = None, order_by = None):
  _get_items(where, order_by)
  return (i for i in cur)

def get_item(vendId):
  cur.execute("SELECT price, quantity, name, category FROM items WHERE vendId = ? LIMIT 1", (vendId,))
  return cur.fetchone()

def get_item_name(vendId):
  cur.execute("SELECT name FROM items WHERE vendId = ? LIMIT 1", (vendId,))
  row = cur.fetchone()
  if row:
    return row[0]

def item_exists(vendId):
  cur.execute("SELECT EXISTS (SELECT 1 FROM items WHERE vendId = ? LIMIT 1)", (vendId,))
  return bool(cur.fetchone()[0])

def new_item(vendId, price, quantity, name, category):
  cur.execute("INSERT OR REPLACE INTO items VALUES (?, ?, ?, ?, ?)", (vendId, price, quantity, name, category))
  update_key()
  conn.commit()

def update_item(vendId, **kwargs):
  if not kwargs: return
  query = "UPDATE items SET"
  for column in kwargs:
    if column not in columns:
      raise BadColumnError()
    query += " %s = ?," % column
  query = query[:-1] + " WHERE vendId = ?"
  cur.execute(query, kwargs.values() + [vendId])
  update_key()
  conn.commit()

def delete_item(vendId):
  cur.execute("DELETE FROM items WHERE vendId = ?", (vendId,))
  update_key()
  conn.commit()

def clear_items():
  cur.execute("DELETE FROM items")
  update_key()
  conn.commit()

def vend_item(vendId):
  cur.execute("UPDATE items SET quantity = quantity -1 WHERE vendId = ?", (vendId,))
  #don't generate a new key here, because the phone will update it's own database alongside the server during vending.
  conn.commit()


## depths

def set_depth(vendId, depth):
  cur.execute("INSERT OR REPLACE INTO depths VALUES (?, ?)", (vendId, depth))

def get_depth(vendId):
  cur.execute("SELECT depth FROM depths WHERE vendId = ? LIMIT 1", (vendId,))
  row = cur.fetchone()
  if row:
    return row[0]

def clear_depth(vendId):
  cur.execute("DELETE FROM depths WHERE vendId = ?", (vendId,))

def refill(vendId):
  cur.execute("UPDATE items SET quantity = " + \
              "( SELECT depths.depth WHERE vendId == items.vendId )" + \
              "WHERE vendId == ?", (vendId,))
