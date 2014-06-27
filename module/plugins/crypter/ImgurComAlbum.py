import re
from module.plugins.internal.SimpleCrypter import SimpleCrypter

class ImgurComAlbum(SimpleCrypter):
  __name__ = "ImgurComAlbum"
  __type__ = "crypter"
  __version__ = "0.2"
  __description__ = """Imgur.com decrypter plugin"""
  __pattern__ = r"http[s]?://imgur\.com/(a|gallery|)[/]?\w{5,7}"
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"

  TITLE_PATTERN = r'(?P<title>.+) - Imgur'
  LINK_PATTERN = r'i\.imgur\.com/\w{7}[s]?\.(?:jpeg|jpg|png|gif|apng)'

  def getLinks(self):
    urls = re.findall(self.LINK_PATTERN, self.html)
    for url in urls:
      urls[urls.index(url)] = "http://"+ re.sub(r'(\w{7})s\.', r'\1.', url)
    urls = list(set(urls))
    return urls
