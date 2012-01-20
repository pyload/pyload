#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster
from module.utils import html_unescape
from urllib import quote, unquote
from time import sleep

class ZeveraCom(Hoster):
    __name__ = "ZeveraCom"
    __version__ = "0.11"
    __type__ = "hoster"
    __pattern__ = r"http://zevera.com/.*"
    __description__ = """zevera.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    api_url = "http://zevera.com/API.ashx"      
    
    def process(self, pyfile): 
        if not self.account:
            self.logError(_("Please enter your zevera.com account or deactivate this plugin"))
            self.fail("No zevera.com account provided")

        self.logDebug("zevera.com: Old URL: %s" % pyfile.url)
        
        last_size = retries = 0
        olink = self.pyfile.url #quote(self.pyfile.url.encode('utf_8'))
        
        for i in range(100):
            self.retData = self.account.loadAPIRequest(self.req, cmd = 'download_request', olink = olink)       
            self.checkAPIErrors(self.retData)
            
            if self.retData['FileInfo']['StatusID'] == 100: 
                break
            elif self.retData['FileInfo']['StatusID'] == 99:
                self.fail('Failed to initialize download (99)')              
            else:               
                if self.retData['FileInfo']['Progress']['BytesReceived'] <= last_size: 
                    if retries >= 6:
                        self.fail('Failed to initialize download (%d)' % self.retData['FileInfo']['StatusID'] )
                    retries += 1
                else:               
                    retries = 0
                
                last_size = self.retData['FileInfo']['Progress']['BytesReceived']
                               
                pyfile.progress = self.retData['FileInfo']['Progress']['Percentage']
                
                self.setWait(self.retData['Update_Wait'])
                self.wait()                
        
        pyfile.progress = 0
        pyfile.name = self.crazyDecode(self.retData['FileInfo']['RealFileName'])
        pyfile.size = self.retData['FileInfo']['FileSizeInBytes'] 
        
        self.retData = self.account.loadAPIRequest(self.req, cmd = 'download_start', FileID = self.retData['FileInfo']['FileID'])
        self.checkAPIErrors(self.retData)
        
        self.download(self.api_url, get = {
            'cmd': "open_stream",
            'login': self.account.loginname,
            'pass': self.account.password,
            'FileID': self.retData['FileInfo']['FileID'],
            'startBytes': 0
            }
        )                        

    def checkAPIErrors(self, retData):
        if not retData: 
            self.fail('Unknown API response')
            
        if retData['ErrorCode']: 
            self.logError(retData['ErrorCode'], retData['ErrorMessage'])
            self.fail('ERROR: ' + retData['ErrorMessage'])
            
        if self.pyfile.size / 1024000 > retData['AccountInfo']['AvailableTODAYTrafficForUseInMBytes']:
            self.logWarning("Not enough data left to download the file")
    
    def crazyDecode(self, ustring):       
        # accepts decoded ie. unicode string - API response is double-quoted, double-utf8-encoded
        # no idea what the proper order of calling these functions would be :-/
        return html_unescape(unquote(unquote(ustring.replace('@DELIMITER@','#'))).encode('raw_unicode_escape').decode('utf-8'))