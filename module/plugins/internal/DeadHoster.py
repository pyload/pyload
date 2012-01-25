from module.plugins.Hoster import Hoster as _Hoster

def create_getInfo(plugin):
    def getInfo(urls):
        for url in urls:
            yield '#N/A: ' + url, 0, 1, url
    return getInfo

class Hoster(_Hoster):
    __name__ = "DeadHoster"
    __type__ = "hoster"
    __pattern__ = r""
    __version__ = "0.1"
    __description__ = """Hoster is no longer available"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    def init(self):
        self.fail("Hoster is no longer available") 