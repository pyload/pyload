from download_thread import Status

class PyLoadFile:
    """ represents the url or file
    """
    def __init__(self, parent, plugin, url):
        self.parent = parent
        self.id = None
	pluginClass = getattr(plugin, plugin.__name__)
        self.plugin = pluginClass(self)
        self.url = url
	self.filename = "filename"
        self.download_folder = ""
        self.status = Status(self.id)
    
    def _get_my_plugin():
        plugins = parent.get_avail_plugins()
        
    
    
