from download_thread import Status

class PyLoadFile:
    """ represents the url or file
    """
    def __init__(self, parent, url):
        self.parent = parent
        self.id = None
        self.plugin = None
        self.url = url
        self.download_folder = ""
        self.status = Status()
    
    def _get_my_plugin():
        plugins = parent.get_avail_plugins()
        
    
    