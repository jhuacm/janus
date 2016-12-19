import ldap3
from base64 import b64encode

LDAP_SERVER = 'janus.acm.jhu.edu'
BASE_DN = 'dc=acm,dc=jhu,dc=edu'

server = ldap3.Server(LDAP_SERVER)
conn = ldap3.Connection(server, lazy=True)

def lookup_hash(hash):
    with conn:
        conn.search(BASE_DN, '(jhuacmDoorCard='+b64encode(hash).decode()+')',
                    ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
                    attributes=ldap3.ALL_ATTRIBUTES)
        return conn.response

def lookup_felica(hashed_id):
    with conn:
        ldap_filter = "(jhuacmFelicaIdm={})".format(b64encode(hashed_id).decode())
        conn.search(BASE_DN, ldap_filter, ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
                    attributes=ldap3.ALL_ATTRIBUTES)
        return conn.response
