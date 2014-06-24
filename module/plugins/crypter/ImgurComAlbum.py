import re
from module.plugins.Crypter import Crypter

class ImgurComAlbum(Crypter):
  __name__ = "ImgurComAlbum"
  __type__ = "crypter"
  __version__ = "0.1"
  __description__ = """Imgur.com decrypter plugin"""
  __pattern__ = r"http[s]?://imgur\.com/(?:a/|gallery/|)\w{5,7}"
  __config__ = []
  __author_name_ = "nath_schwarz"
  __author_mail_ = "nathan.notwhite@gmail.com"
  
  def decrypt(self, pyfile):
    
    html = self.load(pyfile.url)
    
    filetypes = "(?:jpeg|jpg|png|gif|apng)"
    
    raw_urls = re.findall(r'i\.imgur\.com/\w{7}[s]?\.'+filetypes, html)
    
    if raw_urls:
      parsed_urls = set()
      #Iterate over raw_urls and add add the set - uniqizes the urls automatically
      for i, url in enumerate(raw_urls):
        #Add http for BasePlugin and delete lower case 's' (those are thumbnails)
        temp_url = "http://"+url.replace("s", "")
        parsed_urls.add(temp_url)
        self.logDebug('New url: '+temp_url)
      name = "imgurCom_" + re.search(r'imgur\.com/(?:a/|gallery/|)(\w{5,7})', pyfile.url).group(1)
      self.logDebug('Determined name for package: '+name)
      self.packages.append((name, list(parsed_urls), name))
    else:
      self.logInfo('No urls found')
