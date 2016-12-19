#!/usr/bin/python

from os import path, unlink, chmod
from socket import socket, AF_UNIX, SOCK_STREAM
from time import sleep

# Allow to import from Python 3 to get at SOCKET
# (import fails for Python 3)
try:
  from nfc import ContactlessFrontend
except ImportError:
  pass

SOCKET = '/run/acm_janus_contactless.socket'


def open_socket():
  if path.exists(SOCKET):
    unlink(SOCKET)

  sock = socket(AF_UNIX, SOCK_STREAM)
  sock.bind(SOCKET)
  chmod(SOCKET, 0o666)

  return sock


def open_pasori():
  return NfcReader(ContactlessFrontend('usb'))


class NfcReader(object):
  def __init__(self, nfc):
    self._nfc = nfc

  def read(self):
    tag = self._nfc.connect(rdwr={'on-connect': lambda _: False})
    return tag.identifier.encode('hex')


def main():
  socket = open_socket()
  nfc = open_pasori()

  socket.listen(0)
  con, _ = socket.accept()

  while True:
    tag = nfc.read()
    msg = "{}\n".format(tag).encode('utf-8')

    while True:
      try:
        if con.send(msg) == len(msg):
          break
      except IOError:
        pass

      con.close()
      con, _ = socket.accept()

    sleep(0.5)


if __name__ == '__main__':
  main()
