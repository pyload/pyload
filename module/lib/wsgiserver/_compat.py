"""Compatibility code for using Cheroot with various versions of Python."""

import re

import six

if six.PY3:
    def ntob(n, encoding='ISO-8859-1'):
        """Return the native string as bytes in the given encoding."""
        assert_native(n)
        # In Python 3, the native string type is unicode
        return n.encode(encoding)

    def ntou(n, encoding='ISO-8859-1'):
        """Return the native string as unicode with the given encoding."""
        assert_native(n)
        # In Python 3, the native string type is unicode
        return n

    def bton(b, encoding='ISO-8859-1'):
        """Return the byte string as native string in the given encoding."""
        return b.decode(encoding)
else:
    # Python 2
    def ntob(n, encoding='ISO-8859-1'):
        """Return the native string as bytes in the given encoding."""
        assert_native(n)
        # In Python 2, the native string type is bytes. Assume it's already
        # in the given encoding, which for ISO-8859-1 is almost always what
        # was intended.
        return n

    def ntou(n, encoding='ISO-8859-1'):
        """Return the native string as unicode with the given encoding."""
        assert_native(n)
        # In Python 2, the native string type is bytes.
        # First, check for the special encoding 'escape'. The test suite uses
        # this to signal that it wants to pass a string with embedded \uXXXX
        # escapes, but without having to prefix it with u'' for Python 2,
        # but no prefix for Python 3.
        if encoding == 'escape':
            return six.u(
                re.sub(r'\\u([0-9a-zA-Z]{4})',
                       lambda m: six.unichr(int(m.group(1), 16)),
                       n.decode('ISO-8859-1')))
        # Assume it's already in the given encoding, which for ISO-8859-1
        # is almost always what was intended.
        return n.decode(encoding)

    def bton(b, encoding='ISO-8859-1'):
        """Return the byte string as native string in the given encoding."""
        return b


def assert_native(n):
    """Check whether the input is of nativ ``str`` type.

    Raises:
        TypeError: in case of failed check
    """
    if not isinstance(n, str):
        raise TypeError('n must be a native str (got %s)' % type(n).__name__)
