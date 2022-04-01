import time

from send import *
from models import *
import rsa

from sender import send


def get_my_rsa():
    if Key.get_or_none(ip='0.0.0.0') is None:
        my_pub, my_priv = rsa.newkeys(RSA_KEY_LENGTH)
        my = Key.create(ip='0.0.0.0', port=PORT, pub_key=my_pub, priv_key=my_priv)
        members = Member.select()
        mes = {'type': 'pub_key', 'data': str(my_pub)}
        for member in members:
            send((member.ip, PORT), json.dumps(mes))
        return my
    else:
        return Key.get(ip='0.0.0.0')


def get_rsa_key(addr):
    ip, port = addr
    db_key = Key.get_or_none(ip=ip, port=PORT)
    if db_key is not None:
        return db_key
    for a in range(1):
        send(addr, '{"type": "get_pub_key"}')
        for i in range(15):
            time.sleep(0.05)
            db_key = Key.get_or_none(ip=ip, port=PORT)
            if db_key is not None:
                return db_key
    raise Exception("Couldn't get rsa pub_key. Probably served isn't responding")


def get_rsa_pub_from_str(pub):
    n = int(pub.split(",")[0].split("(")[1])
    e = int(pub.split()[1][:-1:])
    return rsa.PublicKey(n, e)


def get_rsa_priv_from_str(pub):
    n = int(pub.split(",")[0].split("(")[1])
    e = int(pub.split()[1][:-1:])
    d = int(pub.split()[2][:-1:])
    p = int(pub.split()[3][:-1:])
    q = int(pub.split()[4][:-1:])
    return rsa.PrivateKey(n, e, d, p, q)
