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

    @author: RaNaN
"""

from module.Api import InteractionTask as BaseInteractionTask
from module.Api import Input, Output

#noinspection PyUnresolvedReferences
class InteractionTask(BaseInteractionTask):
    """
    General Interaction Task extends ITask defined by thrift with additional fields and methods.
    """
    #: Plugins can put needed data here
    storage = None
    #: Timestamp when task expires
    waitUntil = 0
    #: Default data to be used, or True if preset should be used
    default = None
    #: The received result as string representation
    result = None
    #: List of registered handles
    handler = None
    #: Callback functions
    callbacks = None
    #: Error Message
    error = None
    #: Status string
    status = None

    def __init__(self, *args, **kwargs):
        BaseInteractionTask.__init__(self, *args, **kwargs)

        # additional internal attributes
        self.storage = {}
        self.default = []
        self.handler = []
        self.callbacks = []


class CaptchaTask:
    def __init__(self, id, img, format, file, result_type='textual'):
        self.id = str(id)
        self.captchaImg = img
        self.captchaFormat = format
        self.captchaFile = file
        self.captchaResultType = result_type
        self.handler = [] #the hook plugins that will take care of the solution
        self.result = None
        self.waitUntil = None
        self.error = None #error message

        self.status = "init"
        self.data = {} #handler can store data here

    def getCaptcha(self):
        return self.captchaImg, self.captchaFormat, self.captchaResultType

    def setResult(self, text):
        if self.isTextual():
            self.result = text
        if self.isPositional():
            try:
                parts = text.split(',')
                self.result = (int(parts[0]), int(parts[1]))
            except:
                self.result = None

    def getResult(self):
        try:
            res = self.result.encode("utf8", "replace")
        except:
            res = self.result

        return res

    def getStatus(self):
        return self.status

    def setWaiting(self, sec):
        """ let the captcha wait secs for the solution """
        self.waitUntil = max(time() + sec, self.waitUntil)
        self.status = "waiting"

    def isWaiting(self):
        if self.result or self.error or time() > self.waitUntil:
            return False

        return True

    def isTextual(self):
        """ returns if text is written on the captcha """
        return self.captchaResultType == 'textual'

    def isPositional(self):
        """ returns if user have to click a specific region on the captcha """
        return self.captchaResultType == 'positional'

    def setWatingForUser(self, exclusive):
        if exclusive:
            self.status = "user"
        else:
            self.status = "shared-user"

    def timedOut(self):
        return time() > self.waitUntil

    def invalid(self):
        """ indicates the captcha was not correct """
        [x.captchaInvalid(self) for x in self.handler]

    def correct(self):
        [x.captchaCorrect(self) for x in self.handler]

    def __str__(self):
        return "<CaptchaTask '%s'>" % self.id
