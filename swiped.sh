#!/bin/bash

# this script exists to get swiped running under kstart automation.
k5start -f /etc/krb5.keytab -U -t -- /home/localadmin/reader/swiped.py
