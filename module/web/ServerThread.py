#!/usr/bin/env python
import threading
import os
from os.path import join
import subprocess

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.setDaemon(True)
    
    def run(self):
        host = self.pycore.config['webinterface']['host']
        port = self.pycore.config['webinterface']['port']
        self.pycore.logger.info("Starting Webserver: %s:%s" % (host,port) )
        try:
            subprocess.call(['python',join(self.pycore.path,"module","web","manage.py"), "runserver", "%s:%s" % (host,port)], close_fds=True)
        except Exception, e:
            print e
        #os.system("python " + join(self.pycore.path,"module","web","manage.py runserver %s:%s" % (host,port)))
        #@TODO: better would be real python code