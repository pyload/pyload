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

# TODO: config format definition
#       more attributes if needed
#       get rid of catpcha & container plugins ?! (move to crypter & internals)
#       adapt old plugins as needed

class Base(object):
    """
    The Base plugin class with all shared methods and every possible attribute for plugin definition.
    """
    __version__ = "0.1"
    #: Regexp pattern which will be matched for download plugins
    __pattern__ = r""
    #: Flat config definition
    __config__ = tuple()
    #: Short description, one liner
    __description__ = ""
    #: More detailed text
    __long_description__ = """"""
    #: List of needed modules
    __dependencies__ = tuple()
    #: Tags to categorize the plugin
    __tags__ = tuple()
    #: Base64 encoded .png icon
    __icon__ = ""
    #: Alternative, link to png icon
    __icon_url__ = ""
    #: Url with general information/support/discussion
    __url__ = ""
    __author_name__ = tuple()
    __author_mail__ = tuple()


    def __init__(self, core):
        self.__name__ = self.__class__.__name__

        #: Core instance
        self.core = core
        #: logging instance
        self.log = core.log
        #: core config
        self.config = core.config

    #log functions
    def logInfo(self, *args):
        self.log.info("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logWarning(self, *args):
        self.log.warning("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logError(self, *args):
        self.log.error("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))

    def logDebug(self, *args):
        self.log.debug("%s: %s" % (self.__name__, " | ".join([a if isinstance(a, basestring) else str(a) for a in args])))


    def setConf(self, option, value):
        """ see `setConfig` """
        self.core.config.setPlugin(self.__name__, option, value)

    def setConfig(self, option, value):
        """ Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.setConf(option, value)

    def getConf(self, option):
        """ see `getConfig` """
        return self.core.config.getPlugin(self.__name__, option)

    def getConfig(self, option):
        """ Returns config value for current plugin

        :param option:
        :return:
        """
        return self.getConf(option)

    def setStorage(self, key, value):
        """ Saves a value persistently to the database """
        self.core.db.setStorage(self.__name__, key, value)

    def store(self, key, value):
        """ same as `setStorage` """
        self.core.db.setStorage(self.__name__, key, value)

    def getStorage(self, key=None, default=None):
        """ Retrieves saved value or dict of all saved entries if key is None """
        if key is not None:
            return self.core.db.getStorage(self.__name__, key) or default
        return self.core.db.getStorage(self.__name__, key)

    def retrieve(self, *args, **kwargs):
        """ same as `getStorage` """
        return self.getStorage(*args, **kwargs)

    def delStorage(self, key):
        """ Delete entry in db """
        self.core.db.delStorage(self.__name__, key)
