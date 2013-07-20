from module.plugins.Hoster    import Hoster

from module.common.json_layer import json_loads

from module.network.HTTPRequest import BadHeader

class ReloadCc(Hoster):
    __name__ = "ReloadCc"
    __version__ = "0.5"
    __type__ = "hoster"
    __description__ = """Reload.Cc hoster plugin"""

    # Since we want to allow the user to specify the list of hoster to use we let MultiHoster.coreReady create the regex patterns for us using getHosters in our ReloadCc hook.
    __pattern__ = None

    __author_name__ = ("Reload Team")
    __author_mail__ = ("hello@reload.cc")

    def process(self, pyfile):
        # Check account
        if not self.account or not self.account.canUse():
            self.logError(_("Please enter your %s account or deactivate this plugin") % "reload.cc")
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

        query_params = dict(
            via='pyload',
            v=1,
            user=user,
            uri=self.pyfile.url
        )

        try:
            query_params.update(dict(hash=self.account.infos[user]['pwdhash']))
        except Exception:
            query_params.update(dict(pwd=data['password']))

        try:
            answer = self.load("http://api.reload.cc/dl", get=query_params)
        except BadHeader, e:
            if e.code == 400:
                self.fail("The URI is not supported by Reload.cc.")
            elif e.code == 401:
                self.fail("Wrong username or password")
            elif e.code == 402:
                self.fail("Your account is inactive. A payment is required for downloading!")
            elif e.code == 403:
                self.fail("Your account is disabled. Please contact the Reload.cc support!")
            elif e.code == 409:
                self.logWarning("The hoster seems to be a limited hoster and you've used your daily traffic for this hoster: %s" % self.pyfile.url)
                # Wait for 6 hours and retry up to 4 times => one day
                self.retry(max_retries=4, wait_time=(3600 * 6), reason="Limited hoster traffic limit exceeded")
            elif e.code == 429:
                self.retry(max_retries=5, wait_time=120, reason="Too many concurrent connections") # Too many connections, wait 2 minutes and try again
            elif e.code == 503:
                self.retry(wait_time=600, reason="Reload.cc is currently in maintenance mode! Please check again later.") # Retry in 10 minutes
            else:
                self.fail("Internal error within Reload.cc. Please contact the Reload.cc support for further information.")
            return

        data = json_loads(answer)

        # Check status and decide what to do
        status = data.get('status', None)
        if status == "ok":
            conn_limit = data.get('msg', 0)
            # API says these connections are limited
            # Make sure this limit is used - the download will fail if not
            if conn_limit > 0:
                try:
                    self.limitDL = int(conn_limit)
                except ValueError:
                    self.limitDL = 1
            else:
                self.limitDL = 0

            try:
                self.download(data['link'], disposition=True)
            except BadHeader, e:
                if e.code == 404:
                    self.fail("File Not Found")
                elif e.code == 412:
                    self.fail("File access password is wrong")
                elif e.code == 417:
                    self.fail("Password required for file access")
                elif e.code == 429:
                    self.retry(max_retries=5, wait_time=120, reason="Too many concurrent connections") # Too many connections, wait 2 minutes and try again
                else:
                    self.fail("Internal error within Reload.cc. Please contact the Reload.cc support for further information.")
                return
        else:
            self.fail("Internal error within Reload.cc. Please contact the Reload.cc support for further information.")
