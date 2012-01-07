# -*- coding: utf-8 -*-

from time import time

from Account import Account

#noinspection PyUnresolvedReferences
class MultiHoster(Account):
    """
    Base class for MultiHoster services.
    This is also an Account instance so you should see :class:`Account` and overwrite necessary methods.
    Multihoster becomes only active when an Account was entered and the MultiHoster hook was activated.
    You need to overwrite `loadHosterList` and a corresponding :class:`Hoster` plugin with the same name should
    be available to make your service working.
    """

    #: List of hoster names that will be replaced so pyLoad will recognize them: (orig_name, pyload_name)
    replacements = [("freakshare.net", "freakshare.com")]

    #: Load new hoster list every x seconds
    hoster_timeout = 300

    def __init__(self, *args, **kwargs):

        # Hoster list
        self.hoster = []
        # Timestamp
        self.ts = 0

        Account.__init__(*args, **kwargs)

    def loadHosterList(self, req):
        """Load list of supported hoster

        :return: List of domain names
        """
        raise NotImplementedError

    def getHosterList(self, force=False):
        if self.ts + self.hoster_timeout < time() or force:
            req = self.getAccountRequest()
            try:
                self.hoster = self.loadHosterList(req)
            except Exception, e:
                self.logError(e)
                return []
            finally:
                req.close()

            for rep in self.replacements:
                if rep[0] in self.hosters:
                    self.hosters.remove(rep[0])
                    if rep[1] not in self.hosters:
                        self.hosters.append(rep[1])

            self.ts = time()

        return self.hosters