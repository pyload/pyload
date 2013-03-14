# -*- coding: utf-8 -*-

from DBAuth import DBAuth
import subprocess
import os
import threading
import shlex

class ExternalAuth(DBAuth):
    __name__ = "ExternalAuth"
    __version__ = "0.1"
    __description__ = "Authenticates using an external program"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("path", "str", "Path to external authorization program", ""),
                  ("timeout", "int", "timeout for executed program in seconds (-1 for infinite)", "2")]
    __author_name__ = ("jplitza")
    __author_mail__ = ("janphilipp@litza.de")
    
    class Command(object):
        returncode = 1
        
        def __init__(self, core, cmd, env):
            self.cmd = cmd
            self.process = None
            self.env = env
            self.core = core
    
        def run(self, timeout):
            def target():
                self.process = subprocess.Popen(self.cmd,
                                                env=self.env,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT)
                (stdout, stderr) = self.process.communicate()
                if stdout:
                    for line in stdout.splitlines():
                        self.core.log.info("ExternalAuth stdout: %s" % line)
                if stderr:
                    for line in stderr.splitlines():
                        self.core.log.warning("ExternalAuth stderr: %s" % line)
    
            thread = threading.Thread(target=target)
            thread.start()
    
            thread.join(timeout)
            if thread.is_alive():
                self.core.log.warning("ExternalAuth: Killing process after %d seconds" % timeout)
                self.process.terminate()
                # ensure that after a killed process the login fails
                self.returncode = 1
                thread.join()
            self.returncode = self.process.returncode
    
    def checkAuth(self, username, password, remoteip = None):
        env = os.environ
        env['PYLOAD_USERNAME'] = username
        env['PYLOAD_PASSWORD'] = password
        
        cmd = self.Command(self.core, shlex.split(self.getConfig("path")), env)
        cmd.run(timeout=self.getConfig("timeout"))
             
        return username if cmd.returncode == 0 else None