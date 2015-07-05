# -*- coding: utf-8 -*-

from __future__ import with_statement
import httplib
from time import time
import os
import urllib
import simplejson as json

from module.plugins.internal.Hook import Hook, Expose

class WebinterfaceNotify(Hook):
    __name__    = "WebinterfaceNotify"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("activated"              , "bool", "Activated"                                , True ),
                  ("info1"                  , "info", "Timeouts:  -1: 'disable' // 0: 'no timeout' // >0: 'timeout in seconds'", ""   ),
                  ("timeCaptcha"            , "int" , "Captcha Timeout"                         , 0    ),
                  ("timeReconnecting"       , "int" , "Reconnecting Timeout"                    , 0    ),
                  ("timeReconnectFinished"  , "int" , "Reconnect Finished Timeout"              , 5    ),
                  ("timeFileFinished"       , "int" , "File Finished Timeout"                   , -1   ),
                  ("timeFileFailed"         , "int" , "File Failed Timeout"                     , 5    ),
                  ("timePackageFinished"    , "int" , "Package Finished Timeout"                , 5    ),
                  ("timeQueueFinished"      , "int" , "Queue Finished Timeout"                  , 5    ),
                  ("timeQueueFailed"        , "int" , "Queue Failed Timeout"                    , 5    ),
                  ("timePluginsUpdated"     , "int" , "Plugins Updated Timeout"                 , 5    )]

                  #("timePackageFailed"      , "int" , "Package Failed Timeout"                  , 5    ),
                  #("timeLinksCollected"     , "int" , "Links Collected Timeout"                 , 5    ),

    __description__ = """Send pop-up notifications to Webinterface"""
    __license__     = "GPLv3"
    __authors__     = [("Matthias Nippert", "matthias@dornuweb.de")]

    __web_files__ = { 
                        "WebinterfaceNotify.js" : "eyUgYXV0b2VzY2FwZSB0cnVlICV9CnZhciBOb3RpZmljYXRpb25BdmFpbGFibGUsIE5vdGlmaWNhdGlvbkRhdGEsIE5vdGlmaWNhdGlvbkZpcnN0UmVxdWVzdCwgTm90aWZ5TG9hZEpzb25Ub0NvbnRlbnQsIHB5Tm90aWZ5LCByb290OwoKcm9vdCA9IHRoaXM7CgpOb3RpZmljYXRpb25BdmFpbGFibGUgPSBmYWxzZTsKCmlmICgie3tub3RpZmljYXRpb25zLmFjdGl2YXRlZC52YWx1ZX19Ii50b0xvd2VyQ2FzZSgpID09PSAidHJ1ZSIpIHsKICBpZiAodHlwZW9mIE5vdGlmaWNhdGlvbiAhPT0gInVuZGVmaW5lZCIgJiYgTm90aWZpY2F0aW9uICE9PSBudWxsKSB7CiAgICBpZiAoTm90aWZpY2F0aW9uLnBlcm1pc3Npb24gPT09ICJkZWZhdWx0IikgewogICAgICBOb3RpZmljYXRpb24ucmVxdWVzdFBlcm1pc3Npb24oKTsKICAgIH0KICAgIGlmIChOb3RpZmljYXRpb24ucGVybWlzc2lvbiA9PT0gImdyYW50ZWQiKSB7CiAgICAgIE5vdGlmaWNhdGlvbkF2YWlsYWJsZSA9IHRydWU7CiAgICB9CiAgfQp9CgpOb3RpZmljYXRpb25GaXJzdFJlcXVlc3QgPSB0cnVlOwoKcHlOb3RpZnkgPSAoZnVuY3Rpb24oKSB7CiAgZnVuY3Rpb24gcHlOb3RpZnkoYXJnKSB7CiAgICB2YXIgY2xpY2tFdmVudCwgY2xvc2VFdmVudCwgbWVzc2FnZSwgcmVmLCB0YWcsIHRpbWVvdXQ7CiAgICByZWYgPSBhcmcgIT0gbnVsbCA/IGFyZyA6IHt9LCB0YWcgPSByZWYudGFnLCBtZXNzYWdlID0gcmVmLm1lc3NhZ2UsIHRpbWVvdXQgPSByZWYudGltZW91dCwgY2xpY2tFdmVudCA9IHJlZi5jbGlja0V2ZW50LCBjbG9zZUV2ZW50ID0gcmVmLmNsb3NlRXZlbnQ7CiAgICB0aGlzLm9uZ29pbmcgPSBmYWxzZTsKICAgIHRoaXMub2JqZWN0ID0gbnVsbDsKICAgIHRoaXMubGFzdCA9IDA7CiAgICB0aGlzLnRpbWVyID0gbnVsbDsKICAgIHRoaXMudGFnID0gdGFnICE9IG51bGwgPyB0YWcgOiAnJzsKICAgIHRoaXMubWVzc2FnZSA9IG1lc3NhZ2U7CiAgICB0aGlzLnRpbWVvdXQgPSBwYXJzZUludCh0aW1lb3V0KTsKICAgIGlmIChpc05hTih0aGlzLnRpbWVvdXQpKSB7CiAgICAgIHRoaXMudGltZW91dCA9IDU7CiAgICB9CiAgICB0aGlzLnRpbWVvdXQgKj0gMTAwMDsKICAgIHRoaXMuY2xpY2tFdmVudCA9IGNsaWNrRXZlbnQgIT0gbnVsbCA/IGNsaWNrRXZlbnQgOiBudWxsOwogICAgdGhpcy5jbG9zZUV2ZW50ID0gY2xvc2VFdmVudCAhPSBudWxsID8gY2xvc2VFdmVudCA6IG51bGw7CiAgICB0aGlzLmVuYWJsZWQgPSB0aGlzLnRpbWVvdXQgPCAwID8gZmFsc2UgOiB0cnVlOwogIH0KCiAgcHlOb3RpZnkucHJvdG90eXBlLkNyZWF0ZU5vdGlmaWNhdGlvbiA9IGZ1bmN0aW9uKCkgewogICAgaWYgKHRoaXMudGltZW91dCA8IDApIHsKICAgICAgcmV0dXJuOwogICAgfQogICAgaWYgKHRoaXMudGltZXIpIHsKICAgICAgY2xlYXJUaW1lb3V0KHRoaXMudGltZXIpOwogICAgICB0aGlzLnRpbWVyID0gbnVsbDsKICAgIH0KICAgIHRoaXMub2JqZWN0ID0gbmV3IE5vdGlmaWNhdGlvbigncHlMb2FkJywgewogICAgICBpY29uOiAnL21lZGlhL3BsdWdpbnMvV2ViaW50ZXJmYWNlTm90aWZ5L1dlYmludGVyZmFjZU5vdGlmeUxvZ29fc3RhdGljLnBuZycsCiAgICAgIGJvZHk6IHRoaXMubWVzc2FnZSwKICAgICAgdGFnOiB0aGlzLnRhZwogICAgfSk7CiAgICBpZiAodGhpcy5jbGlja0V2ZW50ICE9IG51bGwpIHsKICAgICAgdGhpcy5vYmplY3QuYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCB0aGlzLmNsaWNrRXZlbnQpOwogICAgfQogICAgaWYgKHRoaXMuY2xvc2VFdmVudCAhPSBudWxsKSB7CiAgICAgIHRoaXMub2JqZWN0LmFkZEV2ZW50TGlzdGVuZXIoJ2Nsb3NlJywgdGhpcy5jbG9zZUV2ZW50KTsKICAgIH0KICAgIHRoaXMub25nb2luZyA9IHRydWU7CiAgICBpZiAodGhpcy50aW1lb3V0ID4gMCkgewogICAgICB0aGlzLnRpbWVyID0gc2V0VGltZW91dCgoZnVuY3Rpb24obWUpIHsKICAgICAgICByZXR1cm4gbWUuRGVzdHJveU5vdGlmaWNhdGlvbigpOwogICAgICB9KSwgdGhpcy50aW1lb3V0LCB0aGlzKTsKICAgIH0KICB9OwoKICBweU5vdGlmeS5wcm90b3R5cGUuRGVzdHJveU5vdGlmaWNhdGlvbiA9IGZ1bmN0aW9uKCkgewogICAgdGhpcy5vYmplY3QuY2xvc2UoKTsKICAgIHRoaXMub2JqZWN0ID0gbnVsbDsKICAgIHRoaXMub25nb2luZyA9IGZhbHNlOwogICAgdGhpcy50aW1lciA9IG51bGw7CiAgfTsKCiAgcmV0dXJuIHB5Tm90aWZ5OwoKfSkoKTsKCk5vdGlmaWNhdGlvbkRhdGEgPSB7CiAgY2FwdGNoYTogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ2NhcHRjaGEnLAogICAgbWVzc2FnZTogJ3t7XygiQ2FwdGNoYSB3YWl0aW5nIil9fScsCiAgICBjbGlja0V2ZW50OiAoZnVuY3Rpb24oKSB7CiAgICAgIHJldHVybiAkKCJjYXBfaW5mbyIpLmNsaWNrKCk7CiAgICB9KSwKICAgIHRpbWVvdXQ6ICd7e25vdGlmaWNhdGlvbnMudGltZUNhcHRjaGEudmFsdWV9fScKICB9KSwKICByZWNvbm5lY3Rpbmc6IG5ldyBweU5vdGlmeSh7CiAgICB0YWc6ICdyZWNvbm5lY3QnLAogICAgbWVzc2FnZTogJ3t7XygiUmVjb25uZWN0aW5nLi4uIil9fScsCiAgICB0aW1lb3V0OiAne3tub3RpZmljYXRpb25zLnRpbWVSZWNvbm5lY3RpbmcudmFsdWV9fScKICB9KSwKICByZWNvbm5lY3RGaW5pc2hlZDogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ3JlY29ubmVjdCcsCiAgICBtZXNzYWdlOiAne3tfKCJSZWNvbm5lY3QgY29tcGxldGUhIil9fScsCiAgICB0aW1lb3V0OiAne3tub3RpZmljYXRpb25zLnRpbWVSZWNvbm5lY3RGaW5pc2hlZC52YWx1ZX19JwogIH0pLAogIGZpbGVGaW5pc2hlZDogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ2ZpbGUnLAogICAgbWVzc2FnZTogJ3t7XygiRmlsZSBmaW5pc2hlZCEiKX19JywKICAgIHRpbWVvdXQ6ICd7e25vdGlmaWNhdGlvbnMudGltZUZpbGVGaW5pc2hlZC52YWx1ZX19JwogIH0pLAogIGZpbGVGYWlsZWQ6IG5ldyBweU5vdGlmeSh7CiAgICB0YWc6ICdmaWxlJywKICAgIG1lc3NhZ2U6ICd7e18oIkZpbGUgZmFpbGVkISIpfX0nLAogICAgdGltZW91dDogJ3t7bm90aWZpY2F0aW9ucy50aW1lRmlsZUZhaWxlZC52YWx1ZX19JwogIH0pLAogIHBhY2thZ2VGaW5pc2hlZDogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ3BhY2thZ2UnLAogICAgbWVzc2FnZTogJ3t7XygiUGFja2FnZSBmaW5pc2hlZCEiKX19JywKICAgIHRpbWVvdXQ6ICd7e25vdGlmaWNhdGlvbnMudGltZVBhY2thZ2VGaW5pc2hlZC52YWx1ZX19JwogIH0pLAogIHF1ZXVlRmluaXNoZWQ6IG5ldyBweU5vdGlmeSh7CiAgICB0YWc6ICdxdWV1ZScsCiAgICBtZXNzYWdlOiAne3tfKCJRdWV1ZSBmaW5pc2hlZCEiKX19JywKICAgIHRpbWVvdXQ6ICd7e25vdGlmaWNhdGlvbnMudGltZVF1ZXVlRmluaXNoZWQudmFsdWV9fScKICB9KSwKICBxdWV1ZUZhaWxlZDogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ3F1ZXVlJywKICAgIG1lc3NhZ2U6ICd7e18oIlF1ZXVlIGZhaWxlZCEiKX19JywKICAgIHRpbWVvdXQ6ICd7e25vdGlmaWNhdGlvbnMudGltZVF1ZXVlRmluaXNoZWQudmFsdWV9fScKICB9KSwKICBwbHVnaW5zVXBkYXRlZDogbmV3IHB5Tm90aWZ5KHsKICAgIHRhZzogJ3BsdWdpbnMnLAogICAgbWVzc2FnZTogJ3t7XygiUGx1Z2lucyB1cGRhdGVkISIpfX0nLAogICAgdGltZW91dDogJ3t7bm90aWZpY2F0aW9ucy50aW1lUGx1Z2luc1VwZGF0ZWQudmFsdWV9fScKICB9KQp9OwoKZG9jdW1lbnQuYWRkRXZlbnQoImRvbXJlYWR5IiwgZnVuY3Rpb24oKSB7CiAgcmV0dXJuIG5ldyBSZXF1ZXN0LkpTT04oewogICAgdXJsOiAnL2FwaS9jYWxsP2luZm89JyArIGVuY29kZVVSSUNvbXBvbmVudCgneyJwbHVnaW4iOiJXZWJpbnRlcmZhY2VOb3RpZnkiLCJmdW5jIjoiZ2V0X3RpbWVzdGFtcHMiLCJhcmd1bWVudHMiOk5vbmUsInBhcnNlQXJndW1lbnRzIjpOb25lfScpLAogICAgb25TdWNjZXNzOiBOb3RpZnlMb2FkSnNvblRvQ29udGVudCwKICAgIHNlY3VyZTogZmFsc2UsCiAgICBhc3luYzogdHJ1ZSwKICAgIGluaXRpYWxEZWxheTogMCwKICAgIGRlbGF5OiA0MDAwLAogICAgbGltaXQ6IDMwMDAKICB9KS5zdGFydFRpbWVyKCk7Cn0pOwoKTm90aWZ5TG9hZEpzb25Ub0NvbnRlbnQgPSBmdW5jdGlvbihkYXRhKSB7CiAgdmFyIGV2ZW50LCBuRGF0YSwgdGltZTsKICBkYXRhID0gSlNPTi5wYXJzZShkYXRhKTsKICBpZiAoTm90aWZpY2F0aW9uQXZhaWxhYmxlKSB7CiAgICBmb3IgKGV2ZW50IGluIGRhdGEpIHsKICAgICAgdGltZSA9IGRhdGFbZXZlbnRdOwogICAgICBuRGF0YSA9IE5vdGlmaWNhdGlvbkRhdGFbZXZlbnRdOwogICAgICBpZiAoKG5EYXRhICE9IG51bGwpICYmIG5EYXRhLmxhc3QgPCB0aW1lKSB7CiAgICAgICAgbkRhdGEubGFzdCA9IHRpbWU7CiAgICAgICAgaWYgKCFOb3RpZmljYXRpb25GaXJzdFJlcXVlc3QpIHsKICAgICAgICAgIGlmIChuRGF0YS5lbmFibGVkICYmICFuRGF0YS5vbmdvaW5nKSB7CiAgICAgICAgICAgIG5EYXRhLkNyZWF0ZU5vdGlmaWNhdGlvbigpOwogICAgICAgICAgfQogICAgICAgIH0KICAgICAgfQogICAgICBpZiAoKG5EYXRhICE9IG51bGwpICYmIHRpbWUgPT09IDApIHsKICAgICAgICBuRGF0YS5sYXN0ID0gdGltZTsKICAgICAgICBpZiAobkRhdGEub25nb2luZykgewogICAgICAgICAgbkRhdGEuRGVzdHJveU5vdGlmaWNhdGlvbigpOwogICAgICAgIH0KICAgICAgfQogICAgfQogIH0KICBOb3RpZmljYXRpb25GaXJzdFJlcXVlc3QgPSBmYWxzZTsKICByZXR1cm4gbnVsbDsKfTsKeyUgZW5kYXV0b2VzY2FwZSAlfQo=",
                        "WebinterfaceNotifyLogo_static.png" : "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",
                    }



    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10

        self.lastCaptcha = 0
        self.lastReconnecting = 0
        self.lastReconnectFinished = 0
        self.lastFileFinished = 0
        self.lastFileFailed = 0
        self.lastPackageFinished = 0
        #self.lastPackageFailed = 0
        self.lastQueueFinished = 0
        self.lastQueueFailed = 0
        #self.lastLinksCollected = 0
        self.lastPluginsUpdated = 0
        
    #Refresh respective timestamps.
    #Interpretation of timestamps happens in Webinterface
    def newCaptchaTask(self, task):
        if self.getConfig('timeCaptcha') >= 0:
            self.lastCaptcha = time()
            #This way, we register our calls "captchaCorrect" and "captchaInvalid"
            task.handler.append(self)
    
    def captchaCorrect(self, task):
        self.lastCaptcha = 0

    def captchaInvalid(self, task):
        self.lastCaptcha = 0

    def downloadFinished(self, pyfile):
        if self.getConfig('timeFileFinished') >= 0:
            self.lastFileFinished = time()

    def downloadFailed(self, pyfile):
        if self.getConfig('timeFileFailed') >= 0:
            self.lastFileFailed = time()

    def beforeReconnecting(self, ip):
        if self.getConfig('timeReconnecting') >= 0:
            self.lastReconnecting = time()

    def afterReconnecting(self, ip):
        if self.getConfig('timeReconnectFinished') >= 0:
            self.lastReconnectFinished = time()

    def packageFinished(self, pypack):
        if self.getConfig('timePackageFinished') >= 0:
            self.lastPackageFinished = time()

    def allDownloadsProcessed(self):
        if any(True for pdata in self.core.api.getQueue() if pdata.linksdone < pdata.linkstotal):
            if self.getConfig('timeQueueFailed') >= 0:
                self.lastQueueFailed = time()
                #"One or more packages were not completed successfully"
        else:
            if self.getConfig('timeQueueFinished') >= 0:
                self.lastQueueFinished = time()

    def plugin_updated(self, type_plugins):
        if self.getConfig('timePluginsUpdated') >= 0:
            self.lastPluginsUpdated = time()

    @Expose
    def webinterface_add_plugin_content(self):

        content = [
            {"type":"javascript", "src":"/media/plugins/WebinterfaceNotify/WebinterfaceNotify.js"},
            #{"type":"javascript", "content":"alert('foobar');"},
            #{"type":"css", "content":"body {zoom:0.5}"}
        ]
        return content

    @Expose
    def get_timestamps(self):
        task = self.core.captchaManager.getTask()
        flagCaptcha = 0
        if task is not None:
            flagCaptcha = 1
        
        response = {
            #"captcha":              flagCaptcha,
            "captcha":              self.lastCaptcha,
            "reconnecting":         self.lastReconnecting,
            "reconnectFinished":    self.lastReconnectFinished,
            "fileFinished":         self.lastFileFinished,
            "fileFailed":           self.lastFileFailed,
            "packageFinished":      self.lastPackageFinished,
            #"packageFailed":        self.lastPackageFailed,
            "queueFinished":        self.lastQueueFinished,
            "queueFailed":          self.lastQueueFailed,
            #"linksCollected":       self.lastLinksCollected,
            "pluginsUpdated":       self.lastPluginsUpdated,
        }
        return json.dumps(response)

