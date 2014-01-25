# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

import re

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MultiuploadCom(SimpleCrypter):
    __name__ = "MultiuploadCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?multiupload\.(com|nl)/(?P<ID>\w+)"
    __version__ = "0.02"
    __description__ = """MultiUpload.com crypter"""
    __config__ = [("grab_ddl", "bool", "Grab direct download link", "True"),
                  ("grab_tempoff", "bool", "Grab links not yet fully uploaded", "True"),
                  ("grab_del", "bool", "Grab deleted links", "False"),
                  ("ignored", "str", "List of hosters to ignore (comma separated)", "")]
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    TITLE_PATTERN = r'color:#000000;">(?P<title>.*) <font'

    def getLinks(self):
        links = []

        if self.getConfig("grab_ddl"):
            ddl_pattern = r'<div id="downloadbutton_" style=""><a href="(.+)" id="dlbutton">'
            ddl_found = re.search(ddl_pattern, self.html)
            if ddl_found:
                ddl_url = ddl_found.group(1)
                links.append(ddl_url)

        id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        resource_page = self.load("http://multiupload.com/progress/", get={"d": id})
        resource = json_loads(resource_page)

        ignored_set = set(self.getConfig("ignored").replace(' ', '').split(','))

        for link in resource:
            ready = link["status"] == '1'
            complete = True if self.getConfig("grab_tempoff") else link["progress"] == "100"
            deleted = False if self.getConfig("grab_del") else link["deleted"] == '1'
            ignored = link["service"].lower() in ignored_set

            if ready and complete and not deleted and not ignored:
                header = self.load(link["url"], just_header=True)
                if "location" in header:
                    url = header["location"]
                    links.append(url)

        return links
