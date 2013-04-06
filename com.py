#!/usr/bin/env python2.7

import serial

def read(ser):
  ser.setDTR(False)
  ser.flushInput()
  ser.setDTR(True)
  str = ""
  i = 'G'
  while i != '\r':
    i = ser.read()
    if i != '\n' and i != '\r':
      str = str + i
  ser.setDTR(False)
  ser.flushInput()
  return str

for i in range(1, 10):
  try:
    s = serial.Serial(port = '/dev/com' + str(i), baudrate = 2400, parity = serial.PARITY_NONE, stopbits = 1, 
bytesize = 8)
    break
  except:
    continue

while True:
  print read(s)

s.close()
