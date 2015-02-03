#!/usr/bin/python3

from hash import hash_stripe
from base64 import b64encode
import argparse

import re
import sys
from select import select
import socket
from syslog import syslog

def display_ldif(acmid, stripe):
    print ("dn: cn=%s,dc=acm,dc=jhu,dc=edu" % acmid)
    print ("changetype: modify")
    print ("add: jhuacmDoorCard")
    print ("jhuacmDoorCard: %s" % b64encode(hash_stripe(stripe)))

def lookup_jhed(jhed):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
      s.settimeout(5)
      s.connect("/run/jhu-ldapd.socket")
      s.send(("JHED %s\n" % jhed).encode())
      ret = s.recv(8192).decode().split(" ")

      assert( ret[1] == jhed )
      return ret[2].strip()

def dojhed(acmid, jhedid):
    jcard = lookup_jhed(jhedid)
    print ("# jcard result is %r" % jcard)
    display_ldif(acmid, ";%s0?" % jcard)

def docard(acmid, stripe):
    stripe1 = re.sub(r'^[^;].*[^?]$', r';\g<0>?', stripe)
    stripe2 = re.sub(r'\d\?$', '0?', stripe1, count=1)
    print ("# patched stripe is %r" % stripe2)
    display_ldif(acmid, stripe2)

def main():
  parser = argparse.ArgumentParser(description='Construct LDIF to add jcards')
  parser.add_argument('acm', metavar='acmid', nargs=1, help='ACM user ID')
  parser.add_argument('--jhed', metavar='jhedid', nargs=1, help='JHED ID')
  parser.add_argument('--card', metavar='card read string', nargs=1, help='card read')
  args = parser.parse_args()

  if args.jhed is not None :
    dojhed(args.acm, args.jhed[0])

  if args.card is not None :
    docard(args.acm, args.card[0])

if __name__ == '__main__':
    main()
