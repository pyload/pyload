# -*- coding: utf-8 -*-
from module.plugins.MultiHoster import MultiHoster

import re
from time import mktime, strptime

class ZeveraCom(MultiHoster):
    __name__ = "ZeveraCom"
    __version__ = "0.11"
    __type__ = "account"
    __description__ = """Zevera.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    api_url = "http://zevera.com/API.ashx"     
    
    def loadAccountInfo(self, req):       
        dataRet = self.loadAPIRequest(req)
        account_info = {
            "trafficleft": dataRet['AccountInfo']['AvailableTODAYTrafficForUseInMBytes'] * 1024,
            "validuntil": -1 #dataRet['AccountInfo']['EndSubscriptionDate']            
        }

        return account_info

    def login(self, req):
        if self.loadAPIRequest(req, parse = False) == 'Login Error':
            self.wrongPassword()
        
    def loadHosterList(self, req):
        page = req.load("http://www.zevera.com/jDownloader.ashx?cmd=gethosters")        
        return [x.strip() for x in page.replace("\"", "").split(",")]                                    
    
    def loadAPIRequest(self, req, parse = True, **kwargs):    
        get_dict = {
            'cmd': 'download_request',
            'login': self.loginname,
            'pass': self.password
        }
        get_dict.update(kwargs)

        response = req.load(self.api_url, get = get_dict, decode = True) 
        self.logDebug(response)           
        return self.parseAPIRequest(response) if parse else response
        
    def parseAPIRequest(self, api_response): 
        
        try:
            arFields = iter(api_response.split('TAG BEGIN DATA#')[1].split('#END DATA')[0].split('#'))        
    
            retData = {
                'VersionMajor': arFields.next(),
                'VersionMinor': arFields.next(),
                'ErrorCode': int(arFields.next()),
                'ErrorMessage': arFields.next(),
                'Update_Wait': arFields.next()
            }
            serverInfo = {
                'DateTimeOnServer': mktime(strptime(arFields.next(),"%Y/%m/%d %H:%M:%S")),
                'DAY_Traffic_LimitInMBytes': int(arFields.next())
            }
            accountInfo = {
                'EndSubscriptionDate': mktime(strptime(arFields.next(),"%Y/%m/%d %H:%M:%S")),
                'TrafficUsedInMBytesDayToday': int(arFields.next()),
                'AvailableEXTRATrafficForUseInMBytes': int(arFields.next()),
                'AvailableTODAYTrafficForUseInMBytes': int(arFields.next())
            }
            fileInfo = {
                'FileID': arFields.next(),
                'Title': arFields.next(),
                'RealFileName': arFields.next(),
                'FileNameOnServer': arFields.next(),
                'StorageServerURL': arFields.next(),
                'Token': arFields.next(),
                'FileSizeInBytes': int(arFields.next()),
                'StatusID': int(arFields.next())
            }
            progress = {
                'BytesReceived': int(arFields.next()),
                'TotalBytesToReceive': int(arFields.next()),
                'Percentage': arFields.next(),
                'StatusText': arFields.next(),
                'ProgressText': arFields.next()
            }
            fileInfo.update({
                'Progress': progress,
                'FilePassword': arFields.next(),
                'Keywords': arFields.next(),
                'ImageURL4Download': arFields.next(),
                'CategoryID': arFields.next(),
                'CategoryText': arFields.next(),
                'Notes': arFields.next()
            })
            retData.update({
                'ServerInfo': serverInfo,
                'AccountInfo': accountInfo,
                'FileInfo': fileInfo
            })        
        
        except Exception, e:
            self.logError(e)
            return None    
        
        self.logDebug(retData)
        return retData 