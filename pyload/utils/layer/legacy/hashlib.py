# -*- coding: utf-8 -*-
# @author: vuolter
#
# Hashlib legacy patch

from __future__ import absolute_import, unicode_literals

from hashlib import *

from future import standard_library
from future.builtins import bytes, chr, int, range

standard_library.install_aliases()

try:
    algorithms

except NameError:
    # This tuple and __get_builtin_constructor() must be modified if a new
    # always available algorithm is added.
    __always_supported = (
        'md5',
        'sha1',
        'sha224',
        'sha256',
        'sha384',
        'sha512')

    algorithms_guaranteed = set(__always_supported)
    algorithms_available = set(__always_supported)

    algorithms = __always_supported

    __all__ = __always_supported + ('new', 'algorithms_guaranteed',
                                    'algorithms_available', 'algorithms',
                                    'pbkdf2_hmac')

    try:
        # OpenSSL's PKCS5_PBKDF2_HMAC requires OpenSSL 1.0+ with HMAC and SHA
        from _hashlib import pbkdf2_hmac

    except ImportError:
        import binascii
        import struct

        _trans_5C = b''.join(chr(i ^ 0x5C) for i in range(256))
        _trans_36 = b''.join(chr(i ^ 0x36) for i in range(256))

        def pbkdf2_hmac(hash_name, password, salt, iterations, dklen=None):
            """Password based key derivation function 2 (PKCS #5 v2.0)

            This Python implementations based on the hmac module about
            as fast as OpenSSL's PKCS5_PBKDF2_HMAC for short passwords
            and much faster for long passwords.

            """
            if not isinstance(hash_name, str):
                raise TypeError(hash_name)

            if not isinstance(password, (bytes, bytearray)):
                password = bytes(buffer(password))
            if not isinstance(salt, (bytes, bytearray)):
                salt = bytes(buffer(salt))

            # Fast inline HMAC implementation
            inner = new(hash_name)
            outer = new(hash_name)
            blocksize = getattr(inner, 'block_size', 64)
            if len(password) > blocksize:
                password = new(hash_name, password).digest()
            password = password + b'\x00' * (blocksize - len(password))
            inner.update(password.translate(_trans_36))
            outer.update(password.translate(_trans_5C))

            def prf(msg, inner=inner, outer=outer):
                # PBKDF2_HMAC uses the password as key. We can re-use the same
                # digest objects and just update copies to skip initialization.
                icpy = inner.copy()
                ocpy = outer.copy()
                icpy.update(msg)
                ocpy.update(icpy.digest())
                return ocpy.digest()

            if iterations < 1:
                raise ValueError(iterations)
            if dklen is None:
                dklen = outer.digest_size
            if dklen < 1:
                raise ValueError(dklen)

            hex_format_string = '%%0%ix' % (new(hash_name).digest_size * 2)

            dkey = b''
            loop = 1
            while len(dkey) < dklen:
                prev = prf(salt + struct.pack(b'>I', loop))
                rkey = int(binascii.hexlify(prev), 16)
                for _i in range(iterations - 1):
                    prev = prf(prev)
                    rkey ^= int(binascii.hexlify(prev), 16)
                loop += 1
                dkey += binascii.unhexlify(hex_format_string % rkey)

            return dkey[:dklen]

    # Cleanup locals()
    del __always_supported
