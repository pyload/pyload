# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re

from module.lib.bottle import json_loads
from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FilesmonsterComC(SimpleCrypter):
    __name__ = "FilesmonsterComC"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}\.)?filesmonster\.com/download.php\?id=.*"
    __version__ = "0.01"
    __description__ = """Filesmonster.com Crypter Plugin"""
    __author_name__ = ("igel")
    PREFORM_PATTERN = r"<form id='slowdownload' method=\"post\".*?action=\"(.*?)\">"
    BASE_URL = "http://www.filesmonster.com/"
    JSON_URL_PATTERN = "Event.observe\(window, 'load', function\(\)\{reserve_ticket\('(.*?)'"
    URL_TEMPLATE_PATTERN = "step2UrlTemplate = '(.*?/)!!!/';"
    TEMPORARY_OFFLINE_PATTERN = r"You have started to download"
    NEXT_FILE_WAIT_PATTERN = r"will be available for download in (\d+)"

    def getFileInfo(self):
      m = re.search(self.TEMPORARY_OFFLINE_PATTERN, self.html)
      if m:
        m = re.search(self.NEXT_FILE_WAIT_PATTERN, self.html)
        if m:
          wait_time = 60 * int(m.group(1))
          self.logDebug('need to wait %d sec to download the file' % wait_time)
          # wait time for next file is usually in minutes
          self.setWait(wait_time, reconnect = True)
          self.wait()
          self.retry()
        else:
          self.parseError('error parsing time to wait for the next file')
      else:
        self.logDebug('file can be downloaded')


    def getLinks(self):
      # first, check whether we can download at the moment
      self.getFileInfo()
      # find the link to the linklist
      m = re.search(self.PREFORM_PATTERN, self.html, flags = re.MULTILINE | re.DOTALL)
      if m:
        self.logDebug('loading free URL ' + m.group(1))
        self.html = self.load(self.BASE_URL + m.group(1), decode=True)
      # find the URL template
      m = re.search(self.URL_TEMPLATE_PATTERN, self.html)
      if m:
        url_template = self.BASE_URL + m.group(1)
        self.logDebug('found URL template ' + m.group(1))
        #find the linklist
        m = re.search(self.JSON_URL_PATTERN, self.html)
        if m:
          self.logDebug('reading JSON data from ' + m.group(1))
          json = json_loads(self.load(self.BASE_URL + m.group(1), decode=True))
          links = []
          if json['status'] == 'success':
            for volume in json['volumes']:
              links.append(url_template + volume['dlcode'])
              self.logDebug('adding link with dlcode ' + volume['dlcode'])
            return links
          else:
            #TODO: handle errors
            self.parseError("unhandled error: status " + json['status'])
        else:
          self.parseError("could not find URL template")
      else:
        self.parseError("cound not find JSON link")
