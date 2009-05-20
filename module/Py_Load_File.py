# -*- coding: cp1252 -*-
from download_thread import Status
import re

class PyLoadFile:
    """ represents the url or file
    """
    def __init__(self, parent, url):
        self.parent = parent
        self.id = None
        self.url = url
        self.filename = "filename"
        self.download_folder = ""
        self.modul = __import__(self._get_my_plugin())  
        pluginClass = getattr(self.modul, self.modul.__name__)
        self.plugin = pluginClass(self)
        self.download_folder = ""
        self.status = Status(self)

    
    def _get_my_plugin(self):
        """ searches the right plugin for an url
        """
        for plugin, plugin_pattern in self.parent.plugins_avaible.items():
            if re.match(plugin_pattern, self.url) != None: #guckt ob übergebende url auf muster des plugins passt
                return plugin
        #logger: kein plugin gefunden # was soll passieren wenn nichts gefunden wird?!?
        return None
    
    def prepareDownload(self):
        self.status.exists = self.plugin.file_exists()
	if self.status.exists:
            self.status.filename = self.plugin.get_file_name()
            self.status.waituntil = self.plugin.time_plus_wait
            self.status.url = self.plugin.get_file_url()
            self.status.want_reconnect = self.plugin.want_reconnect

