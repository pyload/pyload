#!/usr/bin/env python
from __future__ import with_statement
import threading
from os.path import join
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from signal import SIGINT
import os

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.running = True
        self.setDaemon(True)
    
    def run(self):
        host = self.pycore.config['webinterface']['host']
        port = self.pycore.config['webinterface']['port']
        command = ['python',join(self.pycore.path,"module","web","manage.py"), "runserver", "%s:%s" % (host,port)]
        self.pycore.logger.info("Starting Webserver: %s:%s" % (host,port) )
        
        if os.name == 'posix':
            self.p = Popen(command, close_fds=True, stderr=PIPE, stdin=PIPE, stdout=PIPE)
            #os.system("python " + join(self.pycore.path,"module","web","manage.py runserver %s:%s" % (host,port)))
            #@TODO: better would be real python code
            sleep(1)
            with open("webserver.pid", "r") as f:
                self.pid = int(f.read().strip())
            while self.running:
                sleep(1)
        else:
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=PIPE)
            while self.running:
                sleep(1)
    
    def quit(self):
        if os.name == 'posix':
            os.kill(self.pid, SIGINT)
        else:
            self.p.kill()
        
        self.running = False
