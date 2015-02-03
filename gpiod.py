#!/usr/bin/python3

from RPi import GPIO as gpio

import os
import socket
from select import select
from syslog import syslog
import time

RELAY_GPIO = 4
SENSOR_GPIO = 25
OPEN_SECONDS = 5.0
LISTENING_SOCKET = '/run/gpiod.socket'

close_time = None

def open_door():
    global close_time
    close_time = time.monotonic() + OPEN_SECONDS
    gpio.output(RELAY_GPIO, True)
    syslog('Door latch was opened.')

def setup():
    gpio.setmode(gpio.BCM)
    gpio.setup(RELAY_GPIO, gpio.OUT)
    gpio.output(RELAY_GPIO, False)
    gpio.setup(SENSOR_GPIO, gpio.IN, gpio.PUD_UP)

def cleanup():
    try:
        gpio.output(RELAY_GPIO, False)
    except Exception:
        pass
    gpio.cleanup()

def main():
    global close_time
    if os.path.exists(LISTENING_SOCKET):
        os.unlink(LISTENING_SOCKET)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind(LISTENING_SOCKET)
    os.chmod(LISTENING_SOCKET, 0o666)

    while True:
        if close_time is None:
            timeout = None
        else:
            timeout = max(0.0, close_time - time.monotonic())
        r, w, e = select([sock], [], [], timeout)
        if sock in r:
            msg, addr = sock.recvfrom(4096)
            if msg == b'OPEN':
                open_door()
            elif msg == b'QUERY':
                sock.sendto(b'OPEN' if gpio.input(SENSOR_GPIO) else b'CLOSED', addr)
        if close_time is not None:
            if time.monotonic() > close_time:
                gpio.output(RELAY_GPIO, False)
                close_time = None

if __name__ == '__main__':
    try:
        setup()
        main()
    finally:
        cleanup()
