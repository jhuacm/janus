#!/usr/bin/env python3

# A script to open the door, using swiped as a library.
# Written by Ben Rosser.

import swipedlib

import syslog

if __name__ == '__main__':
	syslog.syslog('Door opened manually by script.')
	swipedlib.open_door()
