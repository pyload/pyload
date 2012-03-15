# -*- coding: utf-8 -*-
from module.plugins.Account import Account

import re
from time import mktime, strptime

class ZeveraCom(Account):
    __name__ = "ZeveraCom"
    __version__ = "0.20"
    __type__ = "account"
    __description__ = """Zevera.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")    
    
    def loadAccountInfo(self, user, req):       
        data = self.getAPIData(req)
        if data == "No traffic":
            account_info = {"trafficleft": 0, "validuntil": 0, "premium": False}
        else:
            account_info = {
                "trafficleft": int(data['availabletodaytraffic']) * 1024,
                "validuntil": mktime(strptime(data['endsubscriptiondate'],"%Y/%m/%d %H:%M:%S")),
                "premium": True         
            }
        return account_info

    def login(self, user, data, req):
        self.loginname = user
        self.password = data["password"]
        if self.getAPIData(req) == "No traffic":
            self.wrongPassword()
            
    def getAPIData(self, req, just_header = False, **kwargs):
        get_data = {
            'cmd': 'accountinfo',
            'login': self.loginname,
            'pass': self.password
        }
        get_data.update(kwargs)

        response = req.load("http://www.zevera.com/jDownloader.ashx", get = get_data, decode = True, just_header = just_header) 
        self.logDebug(response)

        if ':' in response:
            if not just_header:
                response = response.replace(',','\n')
            return {y.strip().lower(): z.strip() for y,z in [x.split(':',1) for x in response.splitlines() if ':' in x]}
        else:
            return response
        
       
    
    """
    # BitAPI not used - defunct, probably abandoned by Zevera
    
    def loadAccountInfo(self, user, req):       
        dataRet = self.loadAPIRequest(req)
        account_info = {
            "trafficleft": dataRet['AccountInfo']['AvailableTODAYTrafficForUseInMBytes'] * 1024,
            "validuntil": -1 #dataRet['AccountInfo']['EndSubscriptionDate']            
        }

        return account_info

    def login(self, user, data, req):
        self.loginname = user
        self.password = data["password"]
        if self.loadAPIRequest(req, parse = False) == 'Login Error':
            self.wrongPassword()
    
    
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
            
            #self.infos[self.loginname]['trafficleft'] = accountInfo['AvailableTODAYTrafficForUseInMBytes'] * 1024
        
        except Exception, e:
            self.logError(e)
            return None    
        
        self.logDebug(retData)
        return retData
    """ 