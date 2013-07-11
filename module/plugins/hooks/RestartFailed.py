  # -*- coding: utf-8 -*-

'''
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
'''

from module.plugins.Hook import Hook


class RestartFailed(Hook):
    __name__ = 'RestartFailed'
    __version__ = '2.01'
    __description__ = 'Automatically restart failed download'
    __config__ = [
        ('activated', 'bool', 'Activated', 'False'),
        ('rsMode', 'premium + free;only premium', 'Working mode', 'premium + free'),
        ('pWaitime', 'int', 'Premium: retry wait time (min)', '5'),
        ('pTries', 'int', 'Premium: number of maximum retries', '3'),
        ('fWaitime', 'int', 'Free: retry wait time (min)', '30'),
        ('fTries', 'int', 'Free: number of maximum retries', '4'),
        ('rsFirst', 'bool', 'Restart immediately firstly', 'True'),
        ('rsLast', 'once only;repeat;repeat + retry;no', 'Restart after 24 hours lastly', 'once only')
    ]
    __author_name__ = ('Walter Purcaro')
    __author_mail__ = ('vuolter@gmail.com')

    event_map = {'downloadFailed': 'restartFailed'}

    def restartFailed(self, pyfile):
        rsfirst = self.getConfig('rsFirst')
        rslast = self.getConfig('rsLast')
        mode = self.getConfig('rsMode')
        error = pyfile.error
        premium = pyfile.plugin.premium
        if not premium:
            if mode == 'only premium':
                return
            tries = self.getConfig('fTries')
            waitime = self.getConfig('fWaitime')
        else:
            tries = self.getConfig('pTries')
            waitime = self.getConfig('pWaitime')
        self.logDebug('premium: %s , error: %s , tries: %s , waitime: %s min' % (premium, error, tries, waitime))
        msgtime = '%s each time' % waitime
        waitime *= 60
        if error == 'Restart failed' or error == 'Retry failed':
            if rslast == 'no' or (rslast == 'once only' and error == 'Restart failed'):
                return
            elif rslast == 'repeat + retry':
                reason = 'Restart aborted'
            else:
                reason = 'Restart failed'
            tries = 1
            waitime = 86400  #: 24 hours
            msgtime = '24 hours'
        elif error != 'Immediately retry failed' and rsfirst:
            tries = 1
            waitime = 1
            reason = 'Immediately retry failed'
            msgtime = 'one second'
        else:
            reason = 'Restart failed' if rslast == 'no' else 'Retry failed'
        msglog = 'Restart %s , retry %s times, waiting %s'
        self.logInfo(msglog % (pyfile.name, tries, msgtime))
        pyfile.plugin.retry(tries, waitime, reason)
