#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the 
#      Free Software Foundation, Inc., 
#      59 Temple Place, Suite 330, 
#      Boston, MA  02111-1307  USA

# This file is part of urlgrabber, a high-level cross-protocol url-grabber

import httplib
import urllib2

try:
    from M2Crypto import SSL
    from M2Crypto import httpslib
    from M2Crypto import m2urllib2

    have_m2crypto = True
except ImportError:
    have_m2crypto = False

DEBUG = None

if have_m2crypto:
    
    class M2SSLFactory:

        def __init__(self, ssl_ca_cert, ssl_context):
            self.ssl_context = self._get_ssl_context(ssl_ca_cert, ssl_context)

        def _get_ssl_context(self, ssl_ca_cert, ssl_context):
            """
            Create an ssl context using the CA cert file or ssl context.

            The CA cert is used first if it was passed as an option. If not,
            then the supplied ssl context is used. If no ssl context was supplied,
            None is returned.
            """
            if ssl_ca_cert:
                context = SSL.Context()
                context.load_verify_locations(ssl_ca_cert)
                context.set_verify(SSL.verify_peer, -1)
                return context
            else:
                return ssl_context

        def create_https_connection(self, host, response_class = None):
            connection = httplib.HTTPSConnection(host, self.ssl_context)
            if response_class:
                connection.response_class = response_class
            return connection

        def create_opener(self, *handlers):
            return m2urllib2.build_opener(self.ssl_context, *handlers)


class SSLFactory:

    def create_https_connection(self, host, response_class = None):
        connection = httplib.HTTPSConnection(host)
        if response_class:
            connection.response_class = response_class
        return connection

    def create_opener(self, *handlers):
        return urllib2.build_opener(*handlers)

   

def get_factory(ssl_ca_cert = None, ssl_context = None):
    """ Return an SSLFactory, based on if M2Crypto is available. """
    if have_m2crypto:
        return M2SSLFactory(ssl_ca_cert, ssl_context)
    else:
        # Log here if someone provides the args but we don't use them.
        if ssl_ca_cert or ssl_context:
            if DEBUG:
                DEBUG.warning("SSL arguments supplied, but M2Crypto is not available. "
                        "Using Python SSL.")
        return SSLFactory()
