#!/usr/bin/env python2

import remctl
import sys

# this exists because remctl is a python2 library apparently and not a python3 one.
# if I am wrong about this please nuke it and uncomment the code in swipedlib.py

remctlHost = 'gomes.acm.jhu.edu'
remctlPrinc = 'host/gomes.trinidad.acm.jhu.edu'

try:
    message = sys.argv[1]
    if message != '':
        command = ('announce', 'door', message)
        object = remctl.Remctl(remctlHost, 4373, remctlPrinc)
        object.command(command)	
except IndexError:
    pass
