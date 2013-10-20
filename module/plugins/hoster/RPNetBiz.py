from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads
import simplejson

class RPNetBiz(Hoster):
    __name__ = "RPNetBiz"
    __version__ = "0.1"
    __type__ = "hoster"        
    __description__ = """RPNet.Biz hoster plugin"""       
    # Not required as the hook will take care of this.
    __pattern__ = None
    
    __author_name__ = ("Dman")
    __author_mail__ = ("dmanugm@gmail.com")

    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter a valid rpnet.biz account or deactivate this plugin"))
            self.fail("Invalid rpnet.biz account provided")

        # Get account data
        (user, data) = self.account.selectAccount()
                       
        # Get the download link 
        response = self.load("https://premium.rpnet.biz/client_api.php?username=%s&password=%s&action=generate&links=%s" % (user, data['password'], self.pyfile.url))
        link_status = json_loads(response)['links'][0] #get the first link... since we only queried one
        print response
        print link_status

        # Check if we only have an id as a HDD link
        if 'id' in link_status:
            self.setWait(30) #wait for 30 seconds
            self.wait()
            '''Lets query the server again asking for the status on the link, we need to keep doing this until we reach 100'''
            max_tries = 30
            my_try = 0
            success = False
            while (my_try <= max_tries and success is False):
                response = self.load("https://premium.rpnet.biz/client_api.php?username=%s&password=%s&action=downloadInformation&id=%s" % (user, data['password'], link_status['id']))
                download_status = json_loads(response)['download']

                if download_status['status'] == '100':
                    link_status['generated'] = download_status['rpnet_link']
                    success = True
                    continue
                self.setWait(30)
                self.wait()
                my_try = my_try + 1

            if success is False:
                self.fail("Waited for about 15 minutes for download to finish but failed")

        if 'generated' in link_status:
            self.download(link_status['generated'], disposition=True)
        elif 'error' in link_status:
            self.fail(link_status['error'])
        else:
            self.fail("Something went wrong, not supposed to enter here")
