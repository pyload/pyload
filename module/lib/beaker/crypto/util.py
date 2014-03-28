from warnings import warn
from beaker import util


try:
    # Use PyCrypto (if available)
    from Crypto.Hash import HMAC as hmac, SHA as hmac_sha1
    sha1 = hmac_sha1.new

except ImportError:

    # PyCrypto not available.  Use the Python standard library.
    import hmac

    # When using the stdlib, we have to make sure the hmac version and sha
    # version are compatible
    if util.py24:
        from sha import sha as sha1
        import sha as hmac_sha1
    else:
        # NOTE: We have to use the callable with hashlib (hashlib.sha1),
        # otherwise hmac only accepts the sha module object itself
        from hashlib import sha1
        hmac_sha1 = sha1


if util.py24:
    from md5 import md5
else:
    from hashlib import md5
