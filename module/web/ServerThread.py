#!/usr/bin/env python
from __future__ import with_statement
from os.path import exists
from os.path import join
from subprocess import PIPE
from subprocess import Popen
from subprocess import call
from sys import version_info
from cStringIO import StringIO
import threading
import sys

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.pycore = pycore
        self.running = True
        self.server = pycore.config['webinterface']['server']
        self.https = pycore.config['webinterface']['https']
        self.setDaemon(True)
         
    def run(self):
        sys.path.append(join(self.pycore.path, "module", "web"))
        avail = ["builtin"]
        host = self.pycore.config['webinterface']['host']
        port = self.pycore.config['webinterface']['port']
        path = join(self.pycore.path, "module", "web")
        out = StringIO()
        
        if not exists(join(self.pycore.path, "module", "web", "pyload.db")):
            print "########## IMPORTANT ###########"
            print "###        Database for Webinterface does not exitst, it will not be available."
            print "###        Please run: python %s syncdb" % join(self.pycore.path, "module", "web", "manage.py")
            print "###        You have to add at least one User, to gain access to webinterface: python %s createsuperuser" % join(self.pycore.path, "module", "web", "manage.py")
            print "###        Dont forget to restart pyLoad if you are done."
            print "################################"
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
            if exists(self.pycore.config["ssl"]["cert"]) and exists(self.pycore.config["ssl"]["key"]):
                if not exists("ssl.pem"):
                    key = file(self.pycore.config["ssl"]["key"], "rb")
                    cert = file(self.pycore.config["ssl"]["cert"], "rb")

                    pem = file("ssl.pem", "wb")
                    pem.writelines(key.readlines())
                    pem.writelines(cert.readlines())

                    key.close()
                    cert.close()
                    pem.close()

            else:
                self.https = False
        except:
            self.https = False


        if not self.server in avail:
            self.server = "builtin"


        if self.server == "nginx":

            self.pycore.logger.info("Starting nginx Webserver: %s:%s" % (host, port))
            config = file(join(path, "servers", "nginx_default.conf"), "rb")
            content = config.readlines()
            config.close()
            content = "".join(content)

            content = content.replace("%(path)", join(path, "servers"))
            content = content.replace("%(host)", host)
            content = content.replace("%(port)", str(port))
            content = content.replace("%(media)", join(path, "media"))
            content = content.replace("%(version)", ".".join(map(str, version_info[0:2])))

            if self.https:
                content = content.replace("%(ssl)", """
            ssl    on;
            ssl_certificate    %s;
            ssl_certificate_key    %s;
            """ % (self.pycore.config["ssl"]["cert"], self.pycore.config["ssl"]["key"]))
            else:
                content = content.replace("%(ssl)", "")
            
            new_config = file(join(path, "servers", "nginx.conf"), "wb")
            new_config.write(content)
            new_config.close()

            command = ['nginx', '-c', join(path, "servers", "nginx.conf"),]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=Output(out))

            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=9295")


        elif self.server == "lighttpd":
            self.pycore.logger.info("Starting lighttpd Webserver: %s:%s" % (host, port))
            config = file(join(path, "servers", "lighttpd_default.conf"), "rb")
            content = config.readlines()
            config.close()
            content = "".join(content)

            content = content.replace("%(path)", join(path, "servers"))
            content = content.replace("%(host)", host)
            content = content.replace("%(port)", str(port))
            content = content.replace("%(media)", join(path, "media"))
            content = content.replace("%(version)", ".".join(map(str, version_info[0:2])))

            if self.https:
                content = content.replace("%(ssl)", """
            ssl.engine = "enable"
            ssl.pemfile = "%s"
            ssl.ca-file = "%s"
            """ % (join(self.pycore.path, "ssl.pem"), self.pycore.config["ssl"]["cert"]))
            else:
                content = content.replace("%(ssl)", "")
            new_config = file(join(path, "servers", "lighttpd.conf"), "wb")
            new_config.write(content)
            new_config.close()

            command = ['lighttpd', '-D', '-f', join(path, "servers", "lighttpd.conf")]
            self.p = Popen(command, stderr=PIPE, stdin=PIPE, stdout=Output(out))

            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=9295")

         
        elif self.server == "builtin":
            self.pycore.logger.info("Starting django builtin Webserver: %s:%s" % (host, port))

            import run_server
            run_server.handle(host, port)
            #command = ['python', join(self.pycore.path, "module", "web", "run_server.py"), "%s:%s" % (host, port)]
            #self.p = Popen(command, stderr=Output(out), stdin=Output(out), stdout=Output(out))
        else:
            #run fastcgi on port
            import run_fcgi
            run_fcgi.handle("daemonize=false", "method=threaded", "host=127.0.0.1", "port=%s" % str(port))

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