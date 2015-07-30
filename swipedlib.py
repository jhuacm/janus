# Common functions used by swiped and helper scripts.
# Ben Rosser

import socket

def open_door():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.sendto(b'OPEN', '/run/gpiod.socket')
    s.close()

