# -*- coding: utf-8 -*-
# @author: vuolter

import os
from multiprocessing import Process
from builtins import _

# TODO: remove
PYLOAD_API = None


# TODO: make configurable to serve API
class WebServer(Process):
    def __init__(self, core):
        global PYLOAD_API  # make local in future
        
        super(WebServer, self).__init__()
        
        self.pyload = core
        self.app = None
        
        PYLOAD_API = core.api
        
        self.https = core.config.get("webui", "https")  #: recheck
        self.host = core.config.get("webui", "host")
        self.port = core.config.get("webui", "port")
        self.cert = core.config.get("ssl", "cert")
        self.key = core.config.get("ssl", "key")

        self.daemon = True
    
    
    def run(self):
        print("CIAO")
        print("#################################################")
        from pyload.webui import app
        
        self.pyload.log.debug(_("Starting threaded webserver: {host}:{port:d}").format(
                    host=self.host, port=self.port))
                 
        cert = self.cert
        key = self.key
        if self.https and not os.path.isfile(self.cert) or not os.path.isfile(self.key):
            self.pyload.log.warning(_("SSL certificates not found"))
            cert = key = None
                
        self.app = app.run(host=self.host, port=self.port, cert=cert, key=key, debug=self.pyload.debug)
            
            
    # TODO: self-call on shutdown
    def quit(self):
        try:
            self.app.shutdown()
        except AttributeError:
            pass
        