# Common functions used by swiped and helper scripts.
# Ben Rosser

# remctl hooks to open_door are in this file, they should be
# made configurable somewhere presumably.

import os
import socket

#import remctl

def open_door(message=''):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.sendto(b'OPEN', '/run/gpiod.socket')
    s.close()

    # why is remctl in python2 and not python3 yet. :'(
    # anyway, use os.system or something for now...
    if message != '':
        message = '"' + message + '"'
        os.system('k5start -f /etc/krb5.keytab -U -t -- /home/localadmin/reader/python2_remctl_script.py ' + str(message))
#    if message != '':
#        command = ('announce', 'door', message)
#        object = remctl.Remctl(remctlHost, 4373, 'host/hermes.vm.acm.jhu.edu')
#        object.command(command)
