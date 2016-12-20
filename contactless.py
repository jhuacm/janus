#!/usr/bin/python

from sys import exit
from time import sleep
from syslog import syslog
from nfc import ContactlessFrontend # currently requires Python 2 :(
from hash import hash_tag_id
from ldapbackend import lookup_felica
from swipedlib import open_door
from config import OPEN_SECONDS, NFC_VENDOR, NFC_PRODUCT


def build_pasori_frontend():
  return ContactlessFrontend("usb:{}:{}".format(NFC_VENDOR, NFC_PRODUCT))


class NfcReader(object):
  def __init__(self, nfc_factory):
    self._nfc = None
    self._nfc_factory = nfc_factory
    self._build_nfc()

  def read(self):
    while True:
      tag = self._nfc.connect(rdwr={'on-connect': lambda _: False})
      if tag:
        break
      # If tag is falsy, we have lost connection to the NFC reader
      self._build_nfc()

    return tag.identifier.encode('hex')

  def _build_nfc(self):
    if self._nfc:
      self._nfc.close()
    self._nfc = self._nfc_factory()


def try_contactless(tag_id):
  res = lookup_felica(hash_tag_id(bytes(bytearray.fromhex(tag_id))))
  prefix = "Trying card against ACM DB with IDm {}".format(tag_id)

  if res:
      name = res[0]['dn']
      syslog("{} got match {}".format(prefix, name))
      return name
  else:
      syslog("{} got no matches".format(prefix))
      return None


def main():
  try:
    nfc = NfcReader(build_pasori_frontend)
  except Exception as e:
      syslog("Unable to connect to contactless reader: {}".format(e))
    exit(1)

  while True:
    try:
      tag = nfc.read()
      name = try_contactless(tag)
      if name is not None:
        syslog("Door opened by contactless ({})".format(name))
        open_door("{} (NFC!)".format(name))

        # While the card is in proximity, the read events will fire at a fairly
        # rapid rate. To avoid spamming the same card repeatedly, we wait until
        # (about when) the door re-locks to continue polling for cards
        sleep(OPEN_SECONDS)
    except Exception as e:
      syslog("Unexpected contactless exception: {}".format(e))


if __name__ == '__main__':
  main()
