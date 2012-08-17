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
import random
from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads
class C1neonCom(Crypter):
    __name__ = "C1neonCom"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?c1neon.com/.*?"
    __version__ = "0.05"
    __config__ = [
        ("changeNameS", "Packagename;Show;Season;Episode", "Rename Show by", "Show"),
        ("changeName", "Packagename;Movie", "Rename Movie by", "Movie"),
        ("useStreams", "bool", "Use Streams too", False),
        ("hosterListMode", "all;onlypreferred", "Use for hosters (if supported)", "all"),
        ("randomPreferred", "bool", "Randomize Preferred-List", False),
        ("hosterList", "str", "Preferred Hoster list (comma separated, no ending)", "2shared,Bayfiles,Netload,Rapidshare,Share-online"),
        ("ignoreList", "str", "Ignored Hoster list (comma separated, no ending)", "Megaupload")
        ]
    __description__ = """C1neon.Com Container Plugin"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")

    VALUES_PATTERN = r"var subcats = (.*?)(;</script>|;var)"
    SHOW_PATTERN = r"title='(.*?)'"
    SERIE_PATTERN = r"<title>.*Serie.*</title>"
    
    def decrypt(self, pyfile):
        src = self.req.load(str(pyfile.url))

        pattern = re.compile(self.VALUES_PATTERN, re.DOTALL)
        data = json_loads(re.search(pattern, src).group(1))
        
        # Get package info 
        links = []
        Showname = re.search(self.SHOW_PATTERN, src)
        if Showname:
            Showname = Showname.group(1).decode("utf-8")
        else:
            Showname = self.pyfile.package().name
            
        if re.search(self.SERIE_PATTERN, src):
            for Season in data:
                self.logDebug("Season " + Season)
                for Episode in data[Season]:
                    self.logDebug("Episode " + Episode)
                    links.extend(self.getpreferred(data[Season][Episode]))
                    if self.getConfig("changeNameS") == "Episode":
                        self.packages.append((data[Season][Episode]['info']['name'].split("»")[0], links, data[Season][Episode]['info']['name'].split("»")[0]))
                        links = []
                    
                if self.getConfig("changeNameS") == "Season":  
                    self.packages.append((Showname + " Season " + Season, links, Showname + " Season " + Season))
                    links = []

            if self.getConfig("changeNameS") == "Show":
                if  links == []:
                    self.fail('Could not extract any links (Out of Date?)')
                else:
                    self.packages.append((Showname, links, Showname))
        
            elif self.getConfig("changeNameS") == "Packagename":
                if  links == []:
                    self.fail('Could not extract any links (Out of Date?)')
                else:
                    self.core.files.addLinks(links, self.pyfile.package().id)
        else:
            for Movie in data:
                links.extend(self.getpreferred(data[Movie]))
                if self.getConfig("changeName") == "Movie":
                    if  links == []:
                        self.fail('Could not extract any links (Out of Date?)')
                    else:
                        self.packages.append((Showname, links, Showname))
            
                elif self.getConfig("changeName") == "Packagename":
                    if  links == []:
                        self.fail('Could not extract any links (Out of Date?)')
                    else:
                        self.core.files.addLinks(links, self.pyfile.package().id)

    #selects the preferred hoster, after that selects any hoster (ignoring the one to ignore)
    #selects only one Hoster
    def getpreferred(self, hosterslist):
        hosterlist = {}
        if 'u' in hosterslist:
            hosterlist.update(hosterslist['u'])
        if ('d' in hosterslist):
            hosterlist.update(hosterslist['d'])
        if self.getConfig("useStreams") and 's' in hosterslist:
            hosterlist.update(hosterslist['s'])
        
        result = []
        preferredList = self.getConfig("hosterList").strip().lower().replace('|',',').replace('.','').replace(';',',').split(',')
        if self.getConfig("randomPreferred") == True:
            random.shuffle(preferredList)
        for preferred in preferredList:
            for Hoster in hosterlist:
                if preferred == Hoster.split('<')[0].strip().lower().replace('.',''):
                    for Part in hosterlist[Hoster]:
                        self.logDebug("selected " + Part[3])
                        result.append(str(Part[3]))
                    return result

        ignorelist = self.getConfig("ignoreList").strip().lower().replace('|',',').replace('.','').replace(';',',').split(',')
        if self.getConfig('hosterListMode') == "all":
            for Hoster in hosterlist:
                if Hoster.split('<')[0].strip().lower().replace('.','') not in ignorelist:
                    for Part in hosterlist[Hoster]:
                        self.logDebug("selected " + Part[3])
                        result.append(str(Part[3]))
                    return result
        return result
        
        
      
