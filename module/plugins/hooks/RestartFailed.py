# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon


class RestartFailed(Addon):
    __name__    = "RestartFailed"
    __type__    = "hook"
    __version__ = "1.62"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"                , False),
                  ("interval" , "int" , "Check interval in minutes", 90   )]

    __description__ = """Restart all the failed downloads in queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PERIODICAL_INTERVAL = 15 * 60  #: 15 minutes


    def periodical(self):
        self.log_info(_("Restarting all failed downloads..."))
        self.pyload.api.restartFailed()


    def activate(self):
        self.start_periodical(self.get_config('interval') * 60)
