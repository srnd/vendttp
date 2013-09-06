import os, time, random, urllib, hashlib, json

if os.path.exists('settings.py'):
  import settings
else:
  import settings_default as settings

if os.path.exists('credentials.py'):
  import credentials
else:
  raw_input("""!! Fatal Error: Couldn't find credentials file.
!! Please copy `credentials_default.py` as `credentials.py` and add the Vending
!! Machine credentials.
[ENTER] to exit.""")
  exit()

class InsufficientFunds(Exception): pass
class SoldOut(Exception): pass
class BadItem(Exception): pass

def make_creds():
  app_id = credentials.APP_ID
  curtime = str(int(time.time()))
  randint = str(random.randint(0, pow(2, 32) - 1))
  signature = hashlib.sha256(curtime + randint + credentials.PRIVATE_KEY) \
             .hexdigest()
  return app_id, curtime, randint, signature

class URLOpenError(IOError):
  def __init__(self, ioerror):
    IOError.__init__(self, *ioerror.args)

class JSONDecodeError(ValueError):
  def __init__(self, valueerror):
    ValueError.__init__(self, *valueerror.args)

def get(url, get_data = None, post_data = None):
  if get_data != None:
    url += "?" + urllib.urlencode(get_data)
  if post_data != None:
    post_data = urllib.urlencode(post_data)
  try:
    response = urllib.urlopen(url, post_data).read()
  except IOError as e:
    raise URLOpenError(e)
  try:
    return json.loads(response)
  except ValueError as e:
    raise JSONDecodeError(e)
