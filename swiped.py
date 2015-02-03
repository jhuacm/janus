#!/usr/bin/python3

from reader import IDTechHIDReader
from hash import hash_stripe
from ldapbackend import lookup_hash

import re
import sys
from select import select
import socket
from syslog import syslog

devfile = IDTechHIDReader.find()
if devfile is None:
    sys.stderr.write('Could not find the card reader.\n')
    sys.exit(1)

reader = IDTechHIDReader(devfile)

def try_jhed(stripe):
    # Don't spam the JHU card database with things that don't look like jcards
    if not re.match(r'^;601\d{13}\?$', stripe) :
        return None

    # Strip punctuation and last digit
    query = re.sub(r'^;(\d*)\d\?$', r'\1', stripe, count=1)

    syslog("Trying jcard with stripe %s" % stripe)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
      s.settimeout(5)
      s.connect("/run/jhu-ldapd.socket")
      s.send(("LOOK %s\n" % query).encode())
      ret = s.recv(8192).decode().split(" ",1)

      if ret[0] == "ISOK" :
        return ret[1].strip()
      elif ret[0] == "DENY" :
        syslog("Entry found in JHED but is denied: %s", ret[1]);
        return None
      else :
        return None

def try_us(hash) :
    res = lookup_hash(hash)
    if len(res) == 0 :
        return None
    else :
        return res[0]['dn']

def open_door():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.sendto(b'OPEN', '/run/gpiod.socket')
    s.close()

def mangle_stripe(stripe):
    return re.sub(r'\d\?', '0?', stripe, count=1)

methods = [ lambda stripe : try_us(hash_stripe(mangle_stripe(stripe)))
          , lambda stripe : try_us(hash_stripe(stripe))
          , lambda stripe : try_jhed(stripe)
          ]

while True:
    stripe = ''.join(t for t in reader.read_card() if t is not None)

    if len(stripe) == 0 : continue

    for method in methods :
        res = method(stripe)
        if res is not None :
            syslog('Door opened by card swipe (%s)' % res)
            open_door()
            break
    else:
        syslog('Unknown card read: (%r)' % stripe)
