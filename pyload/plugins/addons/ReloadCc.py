from module.plugins.internal.MultiHoster import MultiHoster

from module.common.json_layer      import json_loads
from module.network.RequestFactory import getURL

class ReloadCc(MultiHoster):
    __name__ = "ReloadCc"
    __version__ = "0.3"
    __type__ = "hook"
    __description__ = """Reload.cc hook plugin"""

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __author_name__ = ("Reload Team")
    __author_mail__ = ("hello@reload.cc")

    interval = 0 # Disable periodic calls

    def getHoster(self):
        # If no accounts are available there will be no hosters available
        if not self.account or not self.account.canUse():
            print "ReloadCc: No accounts available"
            return []

        # Get account data
        (user, data) = self.account.selectAccount()

        # Get supported hosters list from reload.cc using the json API v1
        query_params = dict(
            via='pyload',
            v=1,
            get_supported='true',
            get_traffic='true',
            user=user
        )

        try:
            query_params.update(dict(hash=self.account.infos[user]['pwdhash']))
        except Exception:
            query_params.update(dict(pwd=data['password']))

        answer = getURL("http://api.reload.cc/login", get=query_params)
        data = json_loads(answer)


        # If account is not valid thera are no hosters available
        if data['status'] != "ok":
            print "ReloadCc: Status is not ok: %s" % data['status']
            return []

        # Extract hosters from json file
        return data['msg']['supportedHosters']

    def coreReady(self):
        # Get account plugin and check if there is a valid account available
        self.account = self.core.accountManager.getAccountPlugin("ReloadCc")
        if not self.account.canUse():
            self.account = None
            self.logError("Please add a valid reload.cc account first and restart pyLoad.")
            return

        # Run the overwriten core ready which actually enables the multihoster hook
        return MultiHoster.coreReady(self)
