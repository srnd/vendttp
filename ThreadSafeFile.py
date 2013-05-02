#!/usr/bin/env python2.7
import threading

class ThreadSafeFile(object):
  def __init__(self, f):
    self.f = f
    self.lock = threading.RLock()
    self.nesting = 0
    self.tls = threading.local()

  def _getlock(self):
    self.lock.acquire()
    self.nesting += 1

  def _droplock(self):
    nesting = self.nesting
    self.nesting = 0
    for i in range(nesting):
      self.lock.release()

  def __getattr__(self, name):
    if name == 'softspace':
      return self.tls.softspace
    else:
      raise AttributeError(name)

  def __setattr__(self, name, value):
    if name == 'softspace':
      self.tls.softspace = value
    else:
      return object.__setattr__(self, name, value)

  def write(self, data):
    self._getlock()
    self.f.write(data)
    if data == '\n':
      self._droplock()
