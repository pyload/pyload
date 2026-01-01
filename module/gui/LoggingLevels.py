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
"""

import logging

#logging.DEBUG = None
#logging.Logger.debug = None

logging.DEBUG9 = 10
logging.DEBUG8 =  9
logging.DEBUG7 =  8
logging.DEBUG6 =  7
logging.DEBUG5 =  6
logging.DEBUG4 =  5
logging.DEBUG3 =  4
logging.DEBUG2 =  3
logging.DEBUG1 =  2
logging.DEBUG0 =  1

logging.addLevelName(logging.DEBUG9, "DEBUG[9]")
logging.addLevelName(logging.DEBUG8, "DEBUG[8]")
logging.addLevelName(logging.DEBUG7, "DEBUG[7]")
logging.addLevelName(logging.DEBUG6, "DEBUG[6]")
logging.addLevelName(logging.DEBUG5, "DEBUG[5]")
logging.addLevelName(logging.DEBUG4, "DEBUG[4]")
logging.addLevelName(logging.DEBUG3, "DEBUG[3]")
logging.addLevelName(logging.DEBUG2, "DEBUG[2]")
logging.addLevelName(logging.DEBUG1, "DEBUG[1]")
logging.addLevelName(logging.DEBUG0, "DEBUG[0]")

def debug9(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG9):
        self._log(logging.DEBUG9, message, args, **kws)
def debug8(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG8):
        self._log(logging.DEBUG8, message, args, **kws)
def debug7(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG7):
        self._log(logging.DEBUG7, message, args, **kws)
def debug6(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG6):
        self._log(logging.DEBUG6, message, args, **kws)
def debug5(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG5):
        self._log(logging.DEBUG5, message, args, **kws)
def debug4(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG4):
        self._log(logging.DEBUG4, message, args, **kws)
def debug3(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG3):
        self._log(logging.DEBUG3, message, args, **kws)
def debug2(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG2):
        self._log(logging.DEBUG2, message, args, **kws)
def debug1(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG1):
        self._log(logging.DEBUG1, message, args, **kws)
def debug0(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEBUG0):
        self._log(logging.DEBUG0, message, args, **kws)

logging.Logger.debug9 = debug9
logging.Logger.debug8 = debug8
logging.Logger.debug7 = debug7
logging.Logger.debug6 = debug6
logging.Logger.debug5 = debug5
logging.Logger.debug4 = debug4
logging.Logger.debug3 = debug3
logging.Logger.debug2 = debug2
logging.Logger.debug1 = debug1
logging.Logger.debug0 = debug0

