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

import sys
from module.utils.fs import exists, makedirs, join

# TODO
#       more attributes if needed
#       get rid of catpcha & container plugins ?! (move to crypter & internals)
#       adapt old plugins as needed

class Fail(Exception):
    """ raised when failed """

class Retry(Exception):
    """ raised when start again from beginning """

class Base(object):
    """
    The Base plugin class with all shared methods and every possible attribute for plugin definition.
    """
    __version__ = "0.1"
    #: Regexp pattern which will be matched for download plugins
    __pattern__ = r""
    #: Config definition: list of  (name, type, verbose_name, default_value) or
    #: (name, type, verbose_name, short_description, default_value)
    __config__ = tuple()
    #: Short description, one liner
    __description__ = ""
    #: More detailed text
    __long_description__ = """"""
    #: List of needed modules
    __dependencies__ = tuple()
    #: Tags to categorize the plugin
    __tags__ = tuple()
    #: Base64 encoded .png icon, please don't use sizes above ~3KB
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
    def logInfo(self, *args, **kwargs):
        self._log("info", *args, **kwargs)

    def logWarning(self, *args, **kwargs):
        self._log("warning", *args, **kwargs)

    def logError(self, *args, **kwargs):
        self._log("error", *args, **kwargs)

    def logDebug(self, *args, **kwargs):
        self._log("debug", *args, **kwargs)

    def _log(self, level, *args, **kwargs):
        if "sep" in kwargs:
            sep = "%s" % kwargs["sep"]
        else:
            sep = " | "

        getattr(self.log, level)("%s: %s" % (self.__name__, sep.join([a if isinstance(a, basestring) else str(a) for a in args])))

    def setConf(self, option, value):
        """ see `setConfig` """
        self.core.config.set(self.__name__, option, value)

    def setConfig(self, option, value):
        """ Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.setConf(option, value)

    def getConf(self, option):
        """ see `getConfig` """
        return self.core.config.get(self.__name__, option)

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

    def shell(self):
        """ open ipython shell """
        if self.core.debug:
            from IPython import embed
            #noinspection PyUnresolvedReferences
            sys.stdout = sys._stdout
            embed()

    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False):
        """Load content at url and returns it

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param just_header: if True only the header will be retrieved and returned as dict
        :param decode: Wether to decode the output according to http header, should be True in most cases
        :return: Loaded content
        """
        if not hasattr(self, "req"): raise Exception("Plugin type does not have Request attribute.")

        if type(url) == unicode: url = str(url)

        res = self.req.load(url, get, post, ref, cookies, just_header, decode=decode)

        if self.core.debug:
            from inspect import currentframe

            frame = currentframe()
            if not exists(join("tmp", self.__name__)):
                makedirs(join("tmp", self.__name__))

            f = open(
                join("tmp", self.__name__, "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))
                , "wb")
            del frame # delete the frame or it wont be cleaned

            try:
                tmp = res.encode("utf8")
            except:
                tmp = res

            f.write(tmp)
            f.close()

        if just_header:
            #parse header
            header = {"code": self.req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line: continue

                key, none, value = line.partition(":")
                key = key.lower().strip()
                value = value.strip()

                if key in header:
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res

    def fail(self, reason):
        """ fail and give reason """
        raise Fail(reason)