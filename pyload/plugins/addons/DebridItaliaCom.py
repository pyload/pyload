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

from module.plugins.internal.MultiHoster import MultiHoster


class DebridItaliaCom(MultiHoster):
    __name__ = "DebridItaliaCom"
    __version__ = "0.07"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Debriditalia.com hook plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def getHoster(self):
        return ["netload.in", "hotfile.com", "rapidshare.com", "multiupload.com",
                "uploading.com", "megashares.com", "crocko.com", "filepost.com",
                "bitshare.com", "share-links.biz", "putlocker.com", "uploaded.to",
                "speedload.org", "rapidgator.net", "likeupload.net", "cyberlocker.ch",
                "depositfiles.com", "extabit.com", "filefactory.com", "sharefiles.co",
                "ryushare.com", "tusfiles.net", "nowvideo.co", "cloudzer.net", "letitbit.net",
                "easybytez.com", "uptobox.com", "ddlstorage.com"]
