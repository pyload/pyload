import re
from module.plugins.internal.SimpleCrypter import SimpleCrypter

class FilerNetFolder(SimpleCrypter):
  __name__ = "FilerNetFolder"
  __type__ = "crypter"
  __version__ = "0.2"
  __description__ = """Filer.net decrypter plugin"""
  __pattern__ = r"http[s]?://filer\.net/folder/(?P<ID>\w{16})"
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"

  TITLE_PATTERN = r'<h3>(?P<title>.+) - <small'
  LINK_PATTERN = r'/get/(\w{16})'

  def getLinks(self):
    urls = re.findall(LINK_PATTERN, self.html)
    for url in urls:
      urls[urls.index(url)] = "http://filer.net/get/"+re.search(r'\w{16}', url).group(0)
    urls = list(set(urls))
    return urls

