#!/usr/bin/env python
from __future__ import with_statement
from os.path import exists
from os.path import join
from os.path import abspath
from os import makedirs
from subprocess import PIPE
from subprocess import Popen
from subprocess import call
from sys import version_info
from cStringIO import StringIO
import threading
import sys
import logging

core = None
log = logging.getLogger("log")

class WebServer(threading.Thread):
    def __init__(self, pycore):
        global core
        threading.Thread.__init__(self)
        self.core = pycore
        core = pycore
        self.running = True
        self.server = pycore.config['webinterface']['server']
        self.https = pycore.config['webinterface']['https']
        self.setDaemon(True)
         
    def run(self):
        sys.path.append(join(pypath, "module", "web"))
        avail = ["builtin"]
        host = self.core.config['webinterface']['host']
        port = self.core.config['webinterface']['port']
        serverpath = join(pypath, "module", "web")
        path = join(abspath(""), "servers")
        out = StringIO()
        
        if not exists("pyload.db"):
            #print "########## IMPORTANT ###########"
            #print "###        Database for Webinterface does not exitst, it will not be available."
            #print "###        Please run: python %s syncdb" % join(self.pycore.path, "module", "web", "manage.py")
            #print "###        You have to add at least one User, to gain access to webinterface: python %s createsuperuser" % join(self.pycore.path, "module", "web", "manage.py")
            #print "###        Dont forget to restart pyLoad if you are done."
            log.warning(_("Database for Webinterface does not exitst, it will not be available."))
            log.warning(_("Please run: python pyLoadCore.py -s"))
            log.warning(_("Go through the setup and create a database and add an user to gain access."))
            return None

        try:
            import flup
            avail.append("fastcgi")
        except:
            pass

        try:
            call(["lighttpd", "-v"], stdout=PIPE, stderr=PIPE)
            import flup
            avail.append("lighttpd")

        except:
            pass

        try:
            call(["nginx", "-v"], stdout=PIPE, stderr=PIPE)
            import flup
            avail.append("nginx")
        except:
            pass


        try:
            if self.https:
                if exists(self.core.config["ssl"]["cert"]) and exists(self.core.config["ssl"]["key"]):
                    if not exists("ssl.pem"):
                        key = file(self.core.config["ssl"]["key"], "rb")
                        cert = file(self.core.config["ssl"]["cert"], "rb")
    
                        pem = file("ssl.pem", "wb")
                        pem.writelines(key.readlines())
                        pem.writelines(cert.readlines())
    
                        key.close()
                        cert.close()
                        pem.close()
    
                else:
                    log.warning(_("SSL certificates not found."))
                    self.https = False
            else:
                pass
        except:
            self.https = False


        if not self.server in avail:
            log.warning(_("Can't use %(server)s, either python-flup or %(server)s is not installed!") % {"server": self.server})
            self.server = "builtin"


        if self.server == "nginx":

            if not exists(join(path, "nginx")):
                makedirs(join(path, "nginx"))
            
            config = file(join(serverpath, "servers", "nginx_default.conf"), "rb")
            content = config.read()
            config.close()

            content = content.replace("%(path)", join(path, "nginx"))
            content = content.replace("%(host)", host)
            content = content.replace("%(port)", str(port))
            content = content.replace("%(media)", join(serverpath, "media"))
            content = content.replace("%(version)", ".".join(map(str, version_info[0:2])))

            if self.https:
                content = content.replace("%(ssl)", """
            ssl    on;
            ssl_certificate    %s;
            ssl_certificate_key    %s;
            """ % (abspath(self.core.config["ssl"]["cert"]), abspath(self.core.config["ssl"]["key"]) ))
            else:
                content = content.replace("%(ssl)", "")
            
            new_config = file(join(path, "nginx.conf"), "wb")
            new_config.write(content)
            new_config.close()

            command = ['nginx', '-c', join(path, "nginx.conf")]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=Output(out))

            log.info(_("Starting nginx Webserver: %(host)s:%(port)d") % {"host": host, "port": port})
            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=9295")


        elif self.server == "lighttpd":
            
            if not exists(join(path, "lighttpd")):
                makedirs(join(path, "lighttpd"))
            
            
            config = file(join(serverpath, "servers", "lighttpd_default.conf"), "rb")
            content = config.readlines()
            config.close()
            content = "".join(content)

            content = content.replace("%(path)", join("servers", "lighttpd"))
            content = content.replace("%(host)", host)
            content = content.replace("%(port)", str(port))
            content = content.replace("%(media)", join(serverpath, "media"))
            content = content.replace("%(version)", ".".join(map(str, version_info[0:2])))

            if self.https:
                content = content.replace("%(ssl)", """
            ssl.engine = "enable"
            ssl.pemfile = "%s"
            ssl.ca-file = "%s"
            """ % (abspath("ssl.pem") , abspath(self.core.config["ssl"]["cert"])) )
            else:
                content = content.replace("%(ssl)", "")
            new_config = file(join("servers", "lighttpd.conf"), "wb")
            new_config.write(content)
            new_config.close()

            command = ['lighttpd', '-D', '-f', join(path, "lighttpd.conf")]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=Output(out))

            log.info(_("Starting lighttpd Webserver: %(host)s:%(port)d") % {"host": host, "port": port})
            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=9295")

         
        elif self.server == "fastcgi":
            #run fastcgi on port
            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=%s" % str(port))
        else:
            self.core.log.info(_("Starting django builtin Webserver: %(host)s:%(port)d") % {"host": host, "port": port})
            import run_server
            run_server.handle(host, port)

    def quit(self):

        try:
            if self.server == "lighttpd" or self.server == "nginx":
                self.p.kill()
                #self.p2.kill()
                return True

            else:
                #self.p.kill()
                return True
        except:
            pass

        
        self.running = False

class Output:
    def __init__(self, stream):
        self.stream = stream

    def fileno(self):
        return 1

    def write(self, data): # Do nothing
        return None
         #self.stream.write(data)
         #self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
