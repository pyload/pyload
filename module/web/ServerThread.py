#!/usr/bin/env python
import threading
import os
from os.path import join

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.setDaemon(True)
    
    def run(self):
        self.pycore.logger.info("Starting Webserver @ Port 8000")
        os.system("python " + join(self.pycore.path,"module","web","manage.py runserver"))
        #@TODO: really bad approach, better would be real python code, or subprocess