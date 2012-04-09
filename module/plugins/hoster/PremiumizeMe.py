from module.plugins.Hoster    import Hoster

from module.common.json_layer import json_loads

class PremiumizeMe(Hoster):
    __name__ = "PremiumizeMe"
    __version__ = "0.1"
    __type__ = "hoster"        
    __description__ = """Premiumize.Me hoster plugin"""
        
    # Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady create the regex patterns for us using getHosters in our PremiumizeMe hook.
    __pattern__ = ""
    
    __author_name__ = ("Florian Franzen")
    __author_mail__ = ("FlorianFranzen@gmail.com")

    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter a valid premiumize.me account or deactivate this plugin"))
            self.fail("No valid premiumize.me account provided")
        
        # Get account data
        (user, data) = self.account.selectAccount()
                       
        # Get rewritten link using the premiumize.me api v1 (see https://secure.premiumize.me/?show=api)
        answer = self.load("https://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=%s" % (user, data['password'], pyfile.url))
        data = json_loads(answer)                

        # Check status and decide what to do
        status = data['status']
        if status == 200:
            self.download(data['result']['location'])
        elif status == 400:
            self.fail("Invalid link")
        elif status == 404: 
            self.offline()
        elif status >= 500:
            self.tempOffline()
        else:
            self.fail(data['statusmessage'])