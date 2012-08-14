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

    @author: zoidberg
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, PluginParseError
from pycurl import FOLLOWLOCATION
    
class DataportCz(SimpleHoster):
    __name__ = "DataportCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*dataport.cz/file/.*"
    __version__ = "0.35"
    __description__ = """Dataport.cz plugin - free only"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<span itemprop="name">(?P<N>[^<]+)</span>'
    FILE_SIZE_PATTERN = r'<td class="fil">Velikost</td>\s*<td>(?P<S>[^<]+)</td>'
    FILE_OFFLINE_PATTERN = r'<h2>Soubor nebyl nalezen</h2>'
    
    CAPTCHA_URL_PATTERN = r'<section id="captcha_bg">\s*<img src="(.*?)"'   
    FREE_SLOTS_PATTERN = ur'Počet volných slotů: <span class="darkblue">(\d+)</span><br />'

    def handleFree(self):                                    
        captchas = {"1": "jkeG", "2": "hMJQ", "3": "vmEK", "4": "ePQM", "5": "blBd"}
         
        for i in range(60):
            action, inputs = self.parseHtmlForm('free_download_form')
            self.logDebug(action, inputs)
            if not action or not inputs:
                raise PluginParseError('free_download_form')
                
            if "captchaId" in inputs and inputs["captchaId"] in captchas:
                inputs['captchaCode'] = captchas[inputs["captchaId"]]            
            else:
                raise PluginParseError('captcha')
                 
            self.html = self.download("http://dataport.cz%s" % action, post = inputs)
            
            check = self.checkDownload({"captcha": 'alert("\u0160patn\u011b opsan\u00fd k\u00f3d z obr\u00e1zu");',
                                        "slot": 'alert("Je n\u00e1m l\u00edto, ale moment\u00e1ln\u011b nejsou'})
            if check == "captcha":
                raise PluginParseError('invalid captcha')
            elif check == "slot":
                self.logDebug("No free slots - wait 60s and retry")
                self.setWait(60, False)
                self.wait()
                self.html = self.load(self.pyfile.url, decode = True)
                continue
            else:
                break
        
create_getInfo(DataportCz)