#!/usr/bin/python3

import asyncio
import ldap3
import socket
import os
from dns import resolver
from syslog import syslog

BASE_DN = 'ou=PEOPLE,dc=win,dc=ad,dc=jhu,dc=edu'
LISTENING_SOCKET = '/run/jhu-ldapd.socket'
with open("/home/localadmin/reader/jhu-acmjanus.password") as pwf :
  global PASSWORD
  PASSWORD = pwf.readline().rstrip()

def searchLDAP(*ap, **akw) :
  # syslog("Making LDAP query %r %r" % (ap, akw))

  dnsAnswer = resolver.query('_ldap._tcp.win.ad.jhu.edu', 'SRV')
  servers = [ str(rr.target) for rr in dnsAnswer ]

  for server in servers :
    try :
      # syslog("Trying server %s" % server)
      conn = ldap3.Connection( ldap3.Server(server, use_ssl = True, connect_timeout = 5)
                             , user='acmjanus@WIN.AD.JHU.EDU', password=PASSWORD
                             )
      conn.bind()
      conn.search(*ap, **akw)
      res = conn.response
      # syslog ("Returning: %r" % res)
      conn.unbind()
      return res
    except ldap3.LDAPException as e :
      syslog("Server %s threw exception %r" % (server,e))
      pass

  raise EnvironmentError("No LDAP servers reachable") 

def lookup_hash(cstr):
  return searchLDAP(BASE_DN, '(johnshopkinseduhmwbadge='+cstr+')', ldap3.SEARCH_SCOPE_SINGLE_LEVEL, attributes=["ou","eduPersonAffiliation"])

def lookup_jhed_jcard(jstr):
  return searchLDAP(BASE_DN, '(cn='+jstr+')', ldap3.SEARCH_SCOPE_SINGLE_LEVEL, attributes=["ou","eduPersonAffiliation","johnshopkinseduhmwbadge"])

def attr_contains(res,ix,val) :
    return list(map(lambda x:x.lower(), res["attributes"][ix])).index(val)

### XXX Policy?
def is_allowed(res) :
    # Are they comp sci?
    try :
        attr_contains(res, "ou", "computer science")
        return True
    except Exception as e:
        syslog ("... exception while validating: '%r'" % e)

    # Are they custodial?
    try :
        attr_contains(res, "ou", "custodial services")
        return True
    except Exception as e:
        syslog ("... exception while validating: '%r'" % e)

    # Are they staff?
    try :
        attr_contains(res, "eduPersonAffiliation", "staff")
        return True
    except Exception as e:
        syslog ("... exception while validating: '%r'" % e)

    return False

@asyncio.coroutine
def handle_conn(reader, writer):
    try:
        while True:
            data = yield from reader.readline()
            if len(data) == 0 :
                break
            msg = data.decode()
            addr = writer.get_extra_info('peername')

            if addr is None :
                break

            splmsg = msg.split(" ",1)
            cmd = splmsg[0]
            if cmd == "JHED" :
                try :
                    udec = splmsg[1].strip();
                    syslog ("Lookup of JHED %s..." % udec)
                    res = lookup_jhed_jcard(udec)[0];
                    writer.write(
                       ("JHED %s %s\n" %
                                ( udec
                                , res["attributes"]["johnshopkinseduhmwbadge"][0]
                                )
                        ).encode())
                except Exception as e:
                    syslog ("Exception while looking up JHED %s: %r" % (udec, e))
                    try :
                        writer.write("CEXN\n", addr)
                    except Exception :
                        syslog ("Exception while writing exception to %s: %r" % (addr, e))
                        pass
            elif cmd == "LOOK" :
                try :
                    udec = splmsg[1].strip();
                    syslog ("Lookup of card %s..." % udec)
                    res = lookup_hash(udec)[0];
                    if is_allowed(res) :
                        writer.write(("ISOK %s\n" % res["dn"]).encode())
                    else :
                        writer.write(("DENY %s\n" % res["dn"]).encode())
                except Exception as e:
                    syslog ("Exception while looking up %s: %r" % (udec, e))
                    try :
                        writer.write(("CEXN: %r\n" % e).encode())
                    except Exception :
                        syslog ("Exception while writing exception to %s: %r" % (addr, e))
                        pass
            else:
                try :
                   writer.write(("UNKC: %s\n" % message).encode())
                except Exception :
                   syslog ("Exception while failing %s: %r" % (addr, e))
                   pass

            yield from writer.drain()
    finally:
        writer.close()

def main():
    if os.path.exists(LISTENING_SOCKET):
        os.unlink(LISTENING_SOCKET)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(LISTENING_SOCKET)
    os.chmod(LISTENING_SOCKET, 0o666)

    loop = asyncio.get_event_loop()
    coro = asyncio.start_unix_server(handle_conn, sock=sock, loop=loop)
    server = loop.run_until_complete(coro)

    syslog('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == '__main__':
    main()
