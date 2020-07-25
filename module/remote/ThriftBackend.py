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

from module.remote.RemoteManager import BackendBase

from thriftbackend.Processor import Processor
from thriftbackend.Protocol import ProtocolFactory
from thriftbackend.Socket import ServerSocket
from thriftbackend.Transport import TransportFactory
#from thriftbackend.Transport import TransportFactoryCompressed

from thrift.server import TServer

class ThriftBackend(BackendBase):
    def setup(self, host, port):
        processor = Processor(self.core.api)

        key = None
        cert = None

        if self.core.config['ssl']['activated']:
            if exists(self.core.config['ssl']['cert']) and exists(self.core.config['ssl']['key']):
                self.core.log.info(_("Using SSL ThriftBackend"))
                key = self.core.config['ssl']['key']
                cert = self.core.config['ssl']['cert']

        transport = ServerSocket(port, host, key, cert)


#        tfactory = TransportFactoryCompressed()
        tfactory = TransportFactory()
        pfactory = ProtocolFactory()
        
        self.server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
        #self.server = TNonblockingServer.TNonblockingServer(processor, transport, tfactory, pfactory)
        
        #server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    
    def serve(self):
        self.server.serve()
