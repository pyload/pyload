  # -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: Walter Purcaro
"""

from module.plugins.Hook import Hook


class RestartFailed(Hook):
    __name__ = "RestartFailed"
    __version__ = "2.00"
    __description__ = "Automatically restart failed download"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("rsMode", "all;only premium", "Restart when download fails", "all"),
        ("fWaitime", "int", "Free: Retry wait time (min)", "5"),
        ("fTries", "int", "Free: Number of maximum retries", "3"),
        ("pWaitime", "int", "Premium: Retry wait time (min)", "5"),
        ("pTries", "int", "Premium: Number of maximum retries", "3"),
        ("rsFirstly", "bool", "Restart immediately firstly", "True"),
        ("rsLastly", "once only; repeat; repeat all; no", "Restart after 24 hours lastly", "once only")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def downloadFailed(self, pyfile):
        # self.logDebug("self.downloadFailed")
        firstly = self.getConf("rsFirstly")
        lastly = self.getConf("rsLastly")
        mode = self.getConf("rsMode")
        error = pyfile.error
        premium = pyfile.plugin.premium
        if not premium:
            if mode == "only premium":
                return
            tries = self.getConf("fTries")
            waitime = self.getConf("fWaitime")
        else:
            tries = self.getConf("pTries")
            waitime = self.getConf("pWaitime")
        waitime *= 60
        pyfile.error = None
        if error == "Restart failed" or "Retry failed":
            if lastly == "no" or ("once only" and error == "Restart failed"):
                return
            elif "repeat all":
                msg = "Restart aborted"
            else:
                msg = "Restart failed"
            tries = 1
            waitime = 86400  #: 24 hours
        elif not "Immediately retry failed" and firstly:
            tries = 1
            waitime = 1
            msg = "Immediately retry failed"
        else:
            msg = "Restart failed" if lastly == "no" else "Retry failed"
        self.logInfo("Restart %s, retrying %s times, waiting %s minutes each time" % (pyload.name, str(tries), str(waitime)))
        pyfile.plugin.retry(tries, waitime, msg)
