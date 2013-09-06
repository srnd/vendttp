from util import get, make_creds, URLOpenError, JSONDecodeError, \
                 InsufficientFunds
from util import settings

class NotLoggedInError(Exception): pass

class AccountManager:
  NONE = 0
  TEST = 1
  SRND = 2
  GUEST = 3

  def logged_in(self):
    return bool(self.account_type)
  
  def __init__(self):
    self.account_type = AccountManager.NONE
    self.username = None
    self.rfid = None
    self.balance = None

  def log_in(self, rfid):
    if self.account_type == AccountManager.GUEST:
      return False
    if rfid == settings.TESTING_RFID:
      self.account_type = AccountManager.TEST
      self.username = settings.TESTING_USERNAME
      self.rfid = rfid
      self.balance = settings.TESTING_BALANCE
      return True
    else:
      try:
        response = get("http://my.studentrnd.org/api/user/rfid",
                       {'rfid' : rfid})
      except URLOpenError as e:
        print "[Error] Could not connect to http://my.studentrnd.org/"
        return False
      except JSONDecodeError:
        print "Unknown RFID tag: %s" % rfid
        return False
      self.account_type = AccountManager.SRND
      self.username = response['username']
      self.rfid = rfid
      
      url  = "http://my.studentrnd.org/api/balance"
      app_id, curtime, rand, sig = make_creds()
      data = {"application_id": app_id,
              "time": curtime,
              "nonce": rand,
              "username": self.username,
              "signature": sig}
      try:
        self.balance = get(url, data)['balance']
      except URLOpenError as e:
        print "[Error] Could not connect to http://my.studentrnd.org/"
        return False
      except ValueError:
        print "Invalid credentials"
        return False
      return True

  def log_in_guest(self):
    self.account_type = AccountManager.GUEST
    self.username = "Guest"
    self.rfid = None
    self.balance = 0

  def log_out(self):
    self.account_type = AccountManager.NONE
    self.username = None
    self.rfid = None
    self.balance = None

  def deposit(self, amount):
    if not self.logged_in():
      raise NotLoggedInError()
    if self.account_type == AccountManager.SRND:
      app_id, curtime, rand, sig = make_creds()
      url = "http://my.studentrnd.org/api/balance/eft"
      get_data = {"application_id" : app_id,
             "time" : curtime,
             "nonce" : rand,
             "username" : self.username,
             "signature" : sig}
      post_data = {'username' : self.username,
                   'amount': amount,
                   'description': "vending machine deposit",
                   'type': 'deposit'}
      self.balance = get(url, get_data, post_data)['balance']
    else:
      balance += amount

  def withdraw(self, amount, descript = None):
    if not self.logged_in():
      raise NotLoggedInError()
    if self.balance < amount:
      raise InsufficientFunds()
    if self.account_type == AccountManager.SRND:
      app_id, curtime, rand, sig = make_creds()
      url = "http://my.studentrnd.org/api/balance/eft"
      get_data = {"application_id" : app_id,
                  "time" : curtime,
                  "nonce" : rand,
                  "username" : self.username,
                  "signature" : sig}
      post_data = {'username' : self.username,
                   'amount': amount,
                   'description': descript,
                   'type' : 'withdrawl'}
      response = get(url, get_data, post_data)
      self.balance = response['balance']
    else:
      self.balance -= amount
