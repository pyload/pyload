from warnings import warn

from beaker.crypto.pbkdf2 import PBKDF2
from beaker.crypto.pbkdf2 import strxor
from beaker.crypto.util import hmac
from beaker.crypto.util import hmac_sha1
from beaker.crypto.util import md5
from beaker.crypto.util import sha1
from beaker import util

keyLength = None

if util.jython:
    try:
        from beaker.crypto.jcecrypto import getKeyLength, aesEncrypt
        keyLength = getKeyLength()
    except ImportError:
        pass
else:
    try:
        from beaker.crypto.pycrypto import aesDecrypt
        from beaker.crypto.pycrypto import aesEncrypt
        from beaker.crypto.pycrypto import getKeyLength
        keyLength = getKeyLength()
    except ImportError:
        pass

if not keyLength:
    has_aes = False
else:
    has_aes = True

if has_aes and keyLength < 32:
    warn('Crypto implementation only supports key lengths up to %d bits. '
         'Generated session cookies may be incompatible with other '
         'environments' % (keyLength * 8))


def generateCryptoKeys(master_key, salt, iterations):
    # NB: We XOR parts of the keystream into the randomly-generated parts, just
    # in case os.urandom() isn't as random as it should be.  Note that if
    # os.urandom() returns truly random data, this will have no effect on the
    # overall security.
    keystream = PBKDF2(master_key, salt, iterations=iterations)
    cipher_key = keystream.read(keyLength)
    return cipher_key
