#!/bin/bash

k5start -f /etc/krb5.keytab -U -t -- /home/localadmin/reader/contactless.py
