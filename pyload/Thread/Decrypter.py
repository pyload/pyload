# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import traceback

from Queue import Queue
from copy import copy
from pprint import pformat
from sys import exc_info, exc_clear
from time import sleep, time, strftime, gmtime
from types import MethodType

from pyload.Thread.Plugin import PluginThread
from pyload.plugin.Plugin import Abort, Fail, Retry


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
            self.m.core.log.info(_("Decrypting starts: %s") % pyfile.name)
            pyfile.error = ""
            pyfile.plugin.preprocessing(self)

        except NotImplementedError:
            self.m.core.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
            return

        except Fail, e:
            msg = e.args[0]

            if msg == "offline":
                pyfile.setStatus("offline")
                self.m.core.log.warning(
                    _("Download is offline: %s") % pyfile.name)
            else:
                pyfile.setStatus("failed")
                self.m.core.log.error(
                    _("Decrypting failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                pyfile.error = msg

            if self.m.core.debug:
                traceback.print_exc()
            return

        except Abort:
            self.m.core.log.info(_("Download aborted: %s") % pyfile.name)
            pyfile.setStatus("aborted")

            if self.m.core.debug:
                traceback.print_exc()
            return

        except Retry:
            self.m.core.log.info(_("Retrying %s") % pyfile.name)
            retry = True
            return self.run()

        except Exception, e:
            pyfile.setStatus("failed")
            self.m.core.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {
                                  "name": pyfile.name, "msg": str(e)})
            pyfile.error = str(e)

            if self.m.core.debug:
                traceback.print_exc()
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
