#!/usr/bin/python3

import hashlib

import os
from base64 import b64decode, b64encode

_secret_file = os.path.join(os.path.dirname(__file__), 'acmdoor.secret')
_secret = b64decode(open(_secret_file, 'rb').read())

def hash_stripe(stripe):
    return hashlib.pbkdf2_hmac('sha1', stripe.encode(), _secret, 1000, 32)

if __name__ == '__main__':
    try:
        while True:
            print(b64encode(hash_stripe(input().strip())).decode())  # ...might not want to run this with Python 2!
    except EOFError:
        pass
