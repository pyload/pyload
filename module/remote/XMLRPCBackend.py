# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay, RaNaN
"""
from os.path import exists

import module.lib.SecureXMLRPCServer as Server
from module.remote.RemoteManager import BackendBase

class XMLRPCBackend(BackendBase):
    def setup(self, host, port):
        server_addr = (host, port)
        if self.core.config['ssl']['activated']:
            if exists(self.core.config['ssl']['cert']) and exists(self.core.config['ssl']['key']):
                self.core.log.info(_("Using SSL XMLRPCBackend"))
                self.server = Server.SecureXMLRPCServer(server_addr, self.core.config['ssl']['cert'],
                                                        self.core.config['ssl']['key'], self.checkAuth)
            else:
                self.core.log.warning(_("SSL Certificates not found, fallback to auth XMLRPC server"))
                self.server = Server.AuthXMLRPCServer(server_addr, self.checkAuth)
        else:
            self.server = Server.AuthXMLRPCServer(server_addr, self.checkAuth)
       
        self.server.register_instance(self.core.api)
    
    def serve(self):
        self.server.serve_forever()
