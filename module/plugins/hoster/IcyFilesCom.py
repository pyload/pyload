# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: godofdream
"""

import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []
    for url in urls:
        html = getURL(url, decode=True)
        if re.search(IcyFilesCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name = re.search(IcyFilesCom.FILE_NAME_PATTERN, html)
            size = re.search(IcyFilesCom.SIZE_PATTERN, html)
            if name is not None:
                name = name.group(1)
                size = (int(size.group(1)) * 1000000)
                result.append((name, size, 2, url))
    yield result
        
        
class IcyFilesCom(Hoster):
    __name__ = "IcyFilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?icyfiles\.com/(.*)"
    __version__ = "0.04"
    __description__ = """IcyFiles.com plugin - free only"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")

    FILE_NAME_PATTERN = r'<div id="file">(.*?)</div>'
    SIZE_PATTERN = r'<li>(\d+) <span>Size/mb'
    FILE_OFFLINE_PATTERN = r'The requested File cant be found'
    WAIT_LONGER_PATTERN = r'All download tickets are in use\. please try it again in a few seconds'
    WAIT_PATTERN = r'<div class="counter">(\d+)</div>'
    TOOMUCH_PATTERN = r'Sorry dude, you have downloaded too much\. Please wait (\d+) seconds'


    def setup(self):
        self.multiDL = False
        
    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        # check if offline
        if re.search(self.FILE_OFFLINE_PATTERN, self.html):
            self.offline()
        # All Downloadtickets in use
        timmy = re.search(self.WAIT_LONGER_PATTERN, self.html)
        if timmy:
            self.logDebug("waitforfreeslot")
            self.waitForFreeSlot()
        # Wait the waittime
        timmy = re.search(self.WAIT_PATTERN, self.html)
        if timmy:
            self.logDebug("waiting", timmy.group(1))
            self.setWait(int(timmy.group(1)) + 2, False)
            self.wait() 
        # Downloaded to much
        timmy = re.search(self.TOOMUCH_PATTERN, self.html)
        if timmy:
            self.logDebug("too much", timmy.group(1))
            self.setWait(int(timmy.group(1)), True)
            self.wait() 
        # Find Name
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (NAME)")
        pyfile.name = found.group(1)
        # Get the URL
        url = pyfile.url
        found = re.search(self.__pattern__, url)
        if found is None:
            self.fail("Parse error (URL)")
        download_url = "http://icyfiles.com/download.php?key=" + found.group(1)
	self.download(download_url)
        # check download
        check = self.checkDownload({
            "notfound": re.compile(r"^<head><title>404 Not Found</title>$"),
            "skippedcountdown": re.compile(r"^Dont skip the countdown$"),
            "waitforfreeslots": re.compile(self.WAIT_LONGER_PATTERN),
            "downloadedtoomuch": re.compile(self.TOOMUCH_PATTERN)
            })
        if check == "skippedcountdown":
            self.fail("Countdown error")
        elif check == "notfound":
            self.fail("404 Not found")
        elif check == "waitforfreeslots":
            self.waitForFreeSlot()
        elif check == "downloadedtoomuch":
            self.retry()

    def waitForFreeSlot(self):
        self.retry(60, 60, "Wait for free slot")
