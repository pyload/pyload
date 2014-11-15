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

    @author: RaNaN
"""

from Queue import Queue
from threading import Thread
from os import listdir, stat
from os.path import join
from time import sleep, time, strftime, gmtime
from traceback import print_exc, format_exc
from pprint import pformat
from sys import exc_info, exc_clear
from copy import copy
from types import MethodType

from pycurl import error

from pyload.datatype.PyFile import PyFile
from pyload.manager.thread.PluginThread import PluginThread
from pyload.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.packagetools import parseNames
from pyload.utils import safe_join
from pyload.api import OnlineStatus


class DecrypterThread(PluginThread):
    """thread for decrypting"""

    def __init__(self, manager, pyfile):
        """constructor"""
        PluginThread.__init__(self, manager)

        self.active = pyfile
        manager.localThreads.append(self)

        pyfile.setStatus("decrypting")

        self.start()

    def getActiveFiles(self):
        return [self.active]

    def run(self):
        """run method"""

        pyfile = self.active
        retry = False

        try:
            self.m.log.info(_("Decrypting starts: %s") % pyfile.name)
            pyfile.error = ""
            pyfile.plugin.preprocessing(self)

        except NotImplementedError:
            self.m.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
            return

        except Fail, e:
            msg = e.args[0]

            if msg == "offline":
                pyfile.setStatus("offline")
                self.m.log.warning(_("Download is offline: %s") % pyfile.name)
            else:
                pyfile.setStatus("failed")
                self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                pyfile.error = msg

            if self.m.core.debug:
                print_exc()
            return

        except Abort:
            self.m.log.info(_("Download aborted: %s") % pyfile.name)
            pyfile.setStatus("aborted")

            if self.m.core.debug:
                print_exc()
            return

        except Retry:
            self.m.log.info(_("Retrying %s") % pyfile.name)
            retry = True
            return self.run()

        except Exception, e:
            pyfile.setStatus("failed")
            self.m.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
            pyfile.error = str(e)

            if self.m.core.debug:
                print_exc()
                self.writeDebugReport(pyfile)

            return

        finally:
            if not retry:
                pyfile.release()
                self.active = False
                self.m.core.files.save()
                self.m.localThreads.remove(self)
                exc_clear()

        if not retry:
            pyfile.delete()
