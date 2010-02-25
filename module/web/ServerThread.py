#!/usr/bin/env python
from __future__ import with_statement
from os.path import exists
from os.path import join
from subprocess import PIPE
from subprocess import Popen
from subprocess import call
from sys import version_info
import threading
from time import sleep

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.running = True
        self.lighttpd = False
        self.setDaemon(True)
    
    def run(self):
        host = self.pycore.config['webinterface']['host']
        port = self.pycore.config['webinterface']['port']
        path = join(self.pycore.path, "module", "web")
        
        if not exists(join(self.pycore.path, "module", "web", "pyload.db")):
            print "########## IMPORTANT ###########"
            print "###        Database for Webinterface doesnt exitst, it will not be available."
            print "###        Please run: python %s syncdb" % join(self.pycore.path, "module", "web", "manage.py")
            print "###        You have to add at least one User, to gain access to webinterface: python %s createsuperuser" % join(self.pycore.path, "module", "web", "manage.py")
            print "###        Dont forget to restart pyLoad if you are done."
            print "################################"
            return None

        try:
            call(["lighttpd", "-v"], stdout=PIPE, stderr=PIPE)
            import flup
            self.lighttpd = True

        except Exception:
            self.lighttpd = False
            
        if self.lighttpd and self.pycore.config['webinterface']['lighttpd']:
            self.pycore.logger.info("Starting lighttpd Webserver: %s:%s" % (host, port))
            config = file(join(path, "lighttpd", "lighttpd_default.conf"), "rb")
            content = config.readlines()
            config.close()
            content = "".join(content)

            content = content.replace("%(path)", join(path, "lighttpd"))
            content = content.replace("%(host)", host)
            content = content.replace("%(port)", port)
            content = content.replace("%(media)", join(path, "media"))
            content = content.replace("%(version)", ".".join(map(str, version_info[0:2])))

            new_config = file(join(path, "lighttpd", "lighttpd.conf"), "wb")
            new_config.write(content)
            new_config.close()

            command = ['python', join(self.pycore.path, "module", "web", "manage.py"), "runfcgi", "daemonize=false", "method=threaded", "host=127.0.0.1", "port=9295"]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=PIPE)

            command2 = ['lighttpd', '-D', '-f', join(path, "lighttpd", "lighttpd.conf")]
            self.p2 = Popen(command2, stderr=PIPE, stdin=PIPE, stdout=PIPE)

         
        else:
            self.pycore.logger.info("Starting django builtin Webserver: %s:%s" % (host, port))
            
            command = ['python', join(self.pycore.path, "module", "web", "run_server.py"), "%s:%s" % (host, port)]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=PIPE)
            

    def quit(self):

        try:
            if self.lighttpd:
                self.p.kill()
                self.p2.kill()
                return True

            else:
                self.p.kill()
        except:
            pass

        
        self.running = False
