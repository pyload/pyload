# -*- coding: utf-8 -*-

import random
import time
import re

from module.network.HTTPRequest import BadHeader
from ..internal.Hoster import Hoster

class LibGen(Hoster):
    __name__ = "LibGen"
    __type__ = "hoster"
    __version__ = "0.2"
    __status__ = "testing"

    # Only for libgen hosts and URLs that have an MD5
    __pattern__ = r'(?i)https?://([^/]+\.)?(libgen.io|booksdescr.org|booksdl.org|booksdescr.com|lib1.org|library1.org|libgen.pw)/.*\b[a-f0-9]{32}\b'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Plugin for libgen.io, mostly to rewrite the downloaded file names"""
    __license__ = "GPLv3"
    __authors__ = [("Yann Jouanique", "yann.jouanique@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multiDL = False

    def process(self, pyfile):
      # Skip the ad screen and do bulk downloads
      # Ad/detail page formats:
      # http://libgen.io/foreignfiction/item/index.php?md5=fb0c2d8060d2843f0374ce7fbf320c3e
      # https://fiction.booksdescr.com/item/detail/52fa5eec6504ccec196fb8a0ff9b6e68
      # http://booksdescr.org/foreignfiction/ads.php?md5=3607316307d0dc4a5cea3c930889269f
      # http://lib1.org/fiction/e15971f7b239ba82f522aff1eddb2cd1
      # https://fiction.libgen.pw/item/detail/6e9939a3b3eec55bd9f5eb57808b5483

      # fiction.DOMAIN/item/detail/MD5
      # DOMAIN/fiction/MD5
      # DOMAIN/fiction/(item/index|ads).php?md5=MD5
      # 

      # To convert to download links:
      # See all mirrors / link structure at http://libgen.io/mirrors.php
      # http://lib1.org/fiction/[md5]
      # https://fiction.libgen.pw/item/detail/[md5]
      # http://booksdescr.org/foreignfiction/get.php?md5=[md5]
      mirrors = [
        "http://booksdl.org/foreignfiction/get.php?md5={}",
        "http://booksdl.org/get.php?direct=true&md5={}",
      ]
      
      # Get MD5
      match = re.search(r"(?i)(?:/|md5=)(?P<md5>[a-f0-9]{32})\b", pyfile.url)
      if not match:
        self.log_error("Could not extract MD5 from URL "+pyfile.url)
        self.fail("Wrong URL")

      else:
        md5 = match.group('md5')
        self.log_debug("Parsed MD5 hash for this download: "+md5)

        # Loop through mirrors
        found = False
        for mirror in mirrors:
          url = mirror.format(md5)
          self.log_debug("Trying mirror: "+url)
          for _i in range(2):
            try:
              self.log_debug("Download attempt "+str(_i))
              self.download(url, disposition=True)

            except BadHeader, e:
              if e.code not in (400, 401, 403, 404, 410, 500, 503):
                raise

            if self.req.code in (400,404,410):
              self.log_warning("Not found on this mirror, skipping")
              break

            elif self.req.code in (500,503):
              self.log_warning("Temporary server error, retrying...")
              time.sleep(5)

            else:
              self.log_debug("Download successful")
              found = True
              break
        
          # Stop mirror iteration if success
          if found:
            break

        # End of the loop!
        if not found:
          self.log_error("Could not find a working mirror")
          self.fail("No working mirror")
        
        else:
          self.log_debug("End of download loop, checking download")
          self.check_download()



    def check_download(self):
        errmsg = self.scan_download({
            'Html error': re.compile(r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)'),
            'Html file': re.compile(r'\A\s*<!DOCTYPE html'),
            'Request error': re.compile(r'([Aa]n error occured while processing your request)')
        })

        if not errmsg:
            return

        try:
            errmsg += " | " + self.last_check.group(1).strip()

        except Exception:
            pass

        self.log_warning(
            _("Check result: ") + errmsg,
            _("Waiting 1 minute and retry"))
        self.retry(3, 60, errmsg)
