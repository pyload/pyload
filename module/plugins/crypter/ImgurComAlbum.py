import re
from module.plugins.Crypter import Crypter

class ImgurComAlbum(Crypter):
  __name__ = "ImgurComAlbum"
  __type__ = "crypter"
  __version__ = "0.1"
  __description__ = """Imgur.com decrypter plugin"""
  __pattern__ = r"http[s]?://imgur\.com/(?:a|gallery)/\w{5,7}"
  __config__ = []
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"
 
  def decrypt(self, pyfile):
    html = self.load(pyfile.url)
    
    filetypes="(?:jpeg|jpg|png|gif|apng)"
    
    parsed_urls = re.findall(r'i\.imgur\.com/\w{7}\.'+filetypes, html)
   
    if parsed_urls:
      parsed_urls=list(set(parsed_urls))
      for i, url in enumerate(parsed_urls):
        parsed_urls[i] = "http://"+url
      name = "imgurCom_" + re.search(r'imgur\.com/(?:a|gallery)/(\w{5,7})', pyfile.url).group(1)
      self.packages.append((name, parsed_urls, name))
    else:
      self.logInfo('No urls found')
