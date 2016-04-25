#!/usr/bin/env python3

# A script to open the door, using swiped as a library.
# Written by Ben Rosser.

import swipedlib

import os
import sys
import syslog

if __name__ == '__main__':
	syslog.syslog('Door opened manually by script.')
	try:
		message = sys.argv[1]
	except IndexError:
		message = 'automated script'
		remoteUser = os.getenv("REMOTE_USER")
		if remoteUser is not None:
			message += ' ran by ' + str(remoteUser)
	swipedlib.open_door(message)
