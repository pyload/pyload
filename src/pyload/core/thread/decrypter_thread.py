# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

from builtins import str

from pyload.plugins.plugin import Abort, Fail, Retry
from .plugin_thread import PluginThread


class DecrypterThread(PluginThread):
    """
    thread for decrypting.
    """

    def __init__(self, manager, pyfile):
        """
        constructor.
        """
        super().__init__(manager)

        self.active = pyfile
        manager.localThreads.append(self)

        pyfile.setStatus("decrypting")

        self.start()

    def getActiveFiles(self):
        return [self.active]

    def run(self):
        """
        run method.
        """

        pyfile = self.active
        retry = False

        try:
            self.m.log.info(self._("Decrypting starts: {}").format(self.active.name))
            self.active.plugin.preprocessing(self)

        except NotImplementedError:
            self.m.log.error(
                self._("Plugin {} is missing a function.").format(self.active.pluginname)
            )
            return

        except Fail as exc:
            msg = exc.args[0]

            if msg == "offline":
                self.active.setStatus("offline")
                self.m.log.warning(
                    self._("Download is offline: {}").format(self.active.name)
                )
            else:
                self.active.setStatus("failed")
                self.m.log.error(
                    self._("Decrypting failed: {name} | {msg}").format(
                        name=self.active.name, msg=msg
                    )
                )
                self.active.error = msg

            return

        except Abort:
            self.m.log.info(self._("Download aborted: {}").format(pyfile.name))
            pyfile.setStatus("aborted")

            return

        except Retry:
            self.m.log.info(self._("Retrying {}").format(self.active.name))
            retry = True
            return self.run()

        except Exception as exc:
            self.active.setStatus("failed")
            self.m.log.error(
                self._("Decrypting failed: {name} | {msg}").format(
                    name=self.active.name, msg=str(exc)
                )
            )
            self.active.error = str(exc)

            if self.m.pyload.debug:
                self.writeDebugReport(pyfile)

            return

        finally:
            if not retry:
                self.active.release()
                self.active = False
                self.m.pyload.files.save()
                self.m.localThreads.remove(self)
                # exc_clear()

        # self.m.pyload.addonManager.downloadFinished(pyfile)

        # self.m.localThreads.remove(self)
        # self.active.finishIfDone()
        if not retry:
            pyfile.delete()
