from module.plugins.Hoster    import Hoster

from module.common.json_layer import json_loads

class ReloadCc(Hoster):
    __name__ = "ReloadCc"
    __version__ = "0.1.1"
    __type__ = "hoster"
    __description__ = """Reload.Cc hoster plugin"""
        
    # Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady create the regex patterns for us using getHosters in our ReloadCc hook.
    __pattern__ = None
    
    __author_name__ = ("Reload Team")
    __author_mail__ = ("hello@reload.cc")

    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter a valid reload.cc account or deactivate this plugin"))
            self.fail("No valid reload.cc account provided")
        
        # In some cases hostsers do not supply us with a filename at download, so we are going to set a fall back filename (e.g. for freakshare or xfileshare)
        self.pyfile.name = self.pyfile.name.split('/').pop() # Remove everthing before last slash
        
        # Correction for automatic assigned filename: Removing html at end if needed
        suffix_to_remove = ["html", "htm", "php", "php3", "asp", "shtm", "shtml", "cfml", "cfm"]
        temp = self.pyfile.name.split('.')
        if temp.pop() in suffix_to_remove:
            self.pyfile.name = ".".join(temp)

        # Get account data
        (user, data) = self.account.selectAccount()
        
        pwd = "pwd=%s" % data['password']

        try:
            pwd = "hash=%s" % data['pwdhash']
        except Exception:
            pass

        # Get rewritten link using the reload.cc api v1
        answer = self.load("https://api.reload.cc/dl?via=pyload&v=1&user=%s&%s&uri=%s" % (user, pwd, self.pyfile.url))
        data = json_loads(answer)                

        # Check status and decide what to do
        status = data['status']
        if status == "ok":
            self.download(data['link'], disposition=True)
        elif status == 400:
            self.fail("Unsupported URI")
        elif status == 401:
            self.fail("Invalid login")
        elif status == 402:
            self.fail("Payment required")
        elif status == 403:
            self.fail("User is disabled")
        elif status == 404:
            self.offline()
        elif status == 509:
            self.fail("Fairuse traffic exceeded")
        elif status >= 500:
            self.tempOffline()
        else:
            self.fail(data['msg'])
