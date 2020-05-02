"""Collection of exceptions raised and/or processed by Cheroot."""

import errno
import sys


class MaxSizeExceeded(Exception):
    """Exception raised when a client sends more data then acceptable within limit.

    Depends on ``request.body.maxbytes`` config option if used within CherryPy
    """


class NoSSLError(Exception):
    """Exception raised when a client speaks HTTP to an HTTPS socket."""


class FatalSSLAlert(Exception):
    """Exception raised when the SSL implementation signals a fatal alert."""


def plat_specific_errors(*errnames):
    """Return error numbers for all errors in errnames on this platform.

    The 'errno' module contains different global constants depending on
    the specific platform (OS). This function will return the list of
    numeric values for a given list of potential names.
    """
    errno_names = dir(errno)
    nums = [getattr(errno, k) for k in errnames if k in errno_names]
    # de-dupe the list
    return list(dict.fromkeys(nums).keys())


socket_error_eintr = plat_specific_errors('EINTR', 'WSAEINTR')

socket_errors_to_ignore = plat_specific_errors(
    'EPIPE',
    'EBADF', 'WSAEBADF',
    'ENOTSOCK', 'WSAENOTSOCK',
    'ETIMEDOUT', 'WSAETIMEDOUT',
    'ECONNREFUSED', 'WSAECONNREFUSED',
    'ECONNRESET', 'WSAECONNRESET',
    'ECONNABORTED', 'WSAECONNABORTED',
    'ENETRESET', 'WSAENETRESET',
    'EHOSTDOWN', 'EHOSTUNREACH',
)
socket_errors_to_ignore.append('timed out')
socket_errors_to_ignore.append('The read operation timed out')
socket_errors_nonblocking = plat_specific_errors(
    'EAGAIN', 'EWOULDBLOCK', 'WSAEWOULDBLOCK')

if sys.platform == 'darwin':
    socket_errors_to_ignore.extend(plat_specific_errors('EPROTOTYPE'))
    socket_errors_nonblocking.extend(plat_specific_errors('EPROTOTYPE'))
