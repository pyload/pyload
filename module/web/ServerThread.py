#!/usr/bin/env python
import threading
from os.path import join
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from signal import SIGINT

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.running = True
        self.setDaemon(True)
    
    def run(self):
        host = self.pycore.config['webinterface']['host']
        port = self.pycore.config['webinterface']['port']
        self.pycore.logger.info("Starting Webserver: %s:%s" % (host,port) )
        self.p = Popen(['python',join(self.pycore.path,"module","web","manage.py"), "runserver", "%s:%s" % (host,port)], close_fds=True, stderr=PIPE, stdin=PIPE, stdout=PIPE, shell=True)
        #os.system("python " + join(self.pycore.path,"module","web","manage.py runserver %s:%s" % (host,port)))
        #@TODO: better would be real python code
        while self.running:
            sleep(1)
    
    def quit(self):
        self.p.terminate()
        self.running = False
