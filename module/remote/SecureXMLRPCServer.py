# Source: http://sources.gentoo.org/viewcvs.py/gimli/server/SecureXMLRPCServer.py?view=markup
#         which seems to be based on http://www.sabren.net/code/python/SecureXMLRPCServer.py
#
# Changes:
# 	2007-01-06 Christian Hoffmann <ch@hoffie.info>
# 		* Bugfix: replaced getattr by hasattr in the conditional
# 		  (lead to an error otherwise)
# 		* SecureXMLRPCServer: added self.instance = None, otherwise a "wrong"
# 		  exception is raised when calling unknown methods via xmlrpc
# 		* Added HTTP Basic authentication support
# 
# Modified for the Sceradon project
#
# This code is in the public domain
# and is provided AS-IS WITH NO WARRANTY WHATSOEVER.
# $Id: SecureXMLRPCServer.py 5 2007-01-06 17:54:13Z hoffie $

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from OpenSSL import SSL
import SocketServer
import socket
import base64

class SecureSocketServer(SocketServer.TCPServer, SocketServer.ThreadingMixIn):
	def __init__(self, addr, cert, key, requestHandler, verify_cert_func=None):
		SocketServer.TCPServer.__init__(self, addr, requestHandler)
		ctx = SSL.Context(SSL.SSLv23_METHOD)
		if not verify_cert_func and hasattr(self, 'verify_client_cert'):
			verify_cert_func = getattr(self, 'verify_client_cert')
		if verify_cert_func:
			ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cert_func)
		ctx.use_privatekey_file(key)
		ctx.use_certificate_file(cert)
		
		tmpConnection = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
		self.socket = SecureSocketConnection(tmpConnection)
		
		self.server_bind()
		self.server_activate()

	def finish_request(self, request, client_address):
		"""Finish one request by instantiating RequestHandlerClass."""
		self.RequestHandlerClass(request, client_address, self)


class SecureXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
	def __init__(self, request, client_address, server, client_digest=None):
		self.authMap = server.getAuthenticationMap()
		SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)
		self.client_digest = client_digest
	
	def setup(self):
		self.connection = self.request
		self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
		self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
	
	def do_POST(self):
		# authentication
		if self.authMap != None: # explicit None!
			if self.headers.has_key('authorization') and self.headers['authorization'].startswith('Basic '):
				authenticationString = base64.b64decode(self.headers['authorization'].split(' ')[1])
				if authenticationString.find(':') != -1:
					username, password = authenticationString.split(':', 1)
					if self.authMap.has_key(username) and self.verifyPassword(username, password):
						return SimpleXMLRPCRequestHandler.do_POST(self)
			self.send_response(401)
			self.end_headers()
			return False
		return SimpleXMLRPCRequestHandler.do_POST(self)
	
	def verifyPassword(self, username, givenPassword):
		return self.authMap[username] == givenPassword


class SecureXMLRPCServer(SecureSocketServer, SimpleXMLRPCServer):
	def __init__(self, address, cert, key, authenticationMap = None, handler=SecureXMLRPCRequestHandler, verify_cert_func=None):
		self.logRequests = False
		SecureSocketServer.__init__(self, address, cert, key, handler, verify_cert_func)
		# This comes from SimpleXMLRPCServer.__init__()->SimpleXMLRPCDispatcher.__init__()
		self.funcs = {}
		self.instance = None
		self.authenticationMap = authenticationMap
	
	def getAuthenticationMap(self):
		return self.authenticationMap


class SecureSocketConnection:
	def __init__(self, connection):
		self.__dict__["connection"] = connection
	
	def __getattr__(self, name):
		return getattr(self.__dict__["connection"], name)
	
	def __setattr__(self, name, value):
		setattr(self.__dict__["connection"], name, value)
	
	def shutdown(self, how=1):
		self.__dict__["connection"].shutdown()
	
	def accept(self):
		connection, address = self.__dict__["connection"].accept()
		return (SecureSocketConnection(connection), address)
