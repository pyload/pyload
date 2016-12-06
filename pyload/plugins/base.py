# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import unicode_literals
from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
import sys
from time import time, sleep
from random import randint

from pyload.utils import decode
from pyload.utils.fs import exists, makedirs, join, remove


# TODO
#       more attributes if needed
#       get rid of catpcha & container plugins ?! (move to crypter & internals)
#       adapt old plugins as needed
class Fail(Exception):
    """ raised when failed """


class Retry(Exception):
    """ raised when start again from beginning """


class Abort(Exception):
    """ raised when aborted """


class Base(object):
    """
    The Base plugin class with all shared methods and every possible attribute for plugin definition.
    """
    #: Version as string or number
    __version__ = "0.1"
    # Type of the plugin, will be inherited and should not be set!
    __type__ = ""
    #: Regexp pattern which will be matched for download/crypter plugins
    __pattern__ = r""
    #: Internal addon plugin which is always loaded
    __internal__ = False
    #: When True this addon can be enabled by every user
    __user_context__ = False
    #: Config definition: list of  (name, type, label, default_value) or
    #: (name, label, desc, Input(...))
    __config__ = tuple()
    #: Short description, one liner
    __description__ = ""
    #: More detailed text
    __explanation__ = """"""
    #: List of needed modules
    __dependencies__ = tuple()
    #: Used to assign a category for addon plugins
    __category__ = ""
    #: Tags to categorize the plugin, see documentation for further info
    __tags__ = tuple()
    #: Base64 encoded .png icon, should be 32x32, please don't use sizes above ~2KB, for bigger icons use url.
    __icon__ = ""
    #: Alternative, link to png icon
    __icon_url__ = ""
    #: Domain name of the service
    __domain__ = ""
    #: Url with general information/support/discussion
    __url__ = ""
    #: Url to term of content, user is accepting these when using the plugin
    __toc_url__ = ""
    #: Url to service (to buy premium) for accounts
    __ref_url__ = ""

    __author__ = tuple()
    __author_mail__ = tuple()


    def __init__(self, core, owner=None):
        self.__name__ = self.__class__.__name__

        #: Core instance
        self.core = core
        #: logging instance
        self.log = core.log
        #: core config
        self.config = core.config
        #: :class:`EventManager`
        self.evm = core.eventManager
        #: :class:`InteractionManager`
        self.im = core.interactionManager
        if owner is not None:
            #: :class:`Api`, user api when user is set
            self.api = self.core.api.withUserContext(owner)
            if not self.api:
                raise Exception("Plugin running with invalid user")

            #: :class:`User`, user related to this plugin
            self.owner = self.api.user
        else:
            self.api = self.core.api
            self.owner = None

        #: last interaction task
        self.task = None

        #: js engine, see `JsEngine`
        self.js = self.core.js

    def __getitem__(self, item):
        """ Retrieves meta data attribute """
        return getattr(self, "__%s__" % item)

    def logInfo(self, *args, **kwargs):
        """ Print args to log at specific level

        :param args: Arbitrary object which should be logged
        :param kwargs: sep=(how to separate arguments), default = " | "
        """
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

        strings = []
        for obj in args:
            if isinstance(obj, str):
                strings.append(obj)
            elif isinstance(obj, str):
                strings.append(decode(obj))
            else:
                strings.append(str(obj))

        getattr(self.log, level)("%s: %s" % (self.__name__, sep.join(strings)))

    def getName(self):
        """ Name of the plugin class """
        return self.__name__

    @property
    def pattern(self):
        """  Gives the compiled pattern of the plugin """
        return self.core.pluginManager.getPlugin(self.__type__, self.__name__).re

    def setConfig(self, option, value):
        """ Set config value for current plugin """
        self.core.config.set(self.__name__, option, value)

    def getConf(self, option):
        """ see `getConfig` """
        return self.getConfig(option)

    def getConfig(self, option):
        """ Returns config value for current plugin """
        return self.core.config.get(self.__name__, option)

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

    def abort(self):
        """ Check if plugin is in an abort state, is overwritten by subtypes"""
        return False

    def checkAbort(self):
        """  Will be overwritten to determine if control flow should be aborted """
        if self.abort(): raise Abort

    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False):
        """Load content at url and returns it

        :param url: url as string
        :param get: GET as dict
        :param post: POST as dict, list or string
        :param ref: Set HTTP_REFERER header
        :param cookies: use saved cookies
        :param just_header: if True only the header will be retrieved and returned as dict
        :param decode: Whether to decode the output according to http header, should be True in most cases
        :return: Loaded content
        """
        if not hasattr(self, "req"):
            raise Exception("Plugin type does not have Request attribute.")
        self.checkAbort()

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
            except Exception:
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
                    if isinstance(header[key], list):
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res

    def invalidTask(self):
        if self.task:
            self.task.invalid()

    def invalidCaptcha(self):
        self.logDebug("Deprecated method .invalidCaptcha, use .invalidTask")
        self.invalidTask()

    def correctTask(self):
        if self.task:
            self.task.correct()

    def correctCaptcha(self):
        self.logDebug("Deprecated method .correctCaptcha, use .correctTask")
        self.correctTask()

    def decryptCaptcha(self, url, get={}, post={}, cookies=True, forceUser=False, imgtype='jpg',
                       result_type='textual'):
        """ Loads a captcha and decrypts it with ocr, plugin, user input

        :param url: url of captcha image
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param forceUser: if True, ocr is not used
        :param imgtype: Type of the Image
        :param result_type: 'textual' if text is written on the captcha\
        or 'positional' for captcha where the user have to click\
        on a specific region on the captcha

        :return: result of decrypting
        """

        img = self.load(url, get=get, post=post, cookies=cookies)

        id = ("%.2f" % time())[-6:].replace(".", "")
        temp_file = open(join("tmp", "tmpCaptcha_%s_%s.%s" % (self.__name__, id, imgtype)), "wb")
        temp_file.write(img)
        temp_file.close()

        name = "%sOCR" % self.__name__
        has_plugin = name in self.core.pluginManager.getPlugins("internal")

        if self.core.captcha:
            OCR = self.core.pluginManager.loadClass("internal", name)
        else:
            OCR = None

        if OCR and not forceUser:
            sleep(old_div(randint(3000, 5000), 1000.0))
            self.checkAbort()

            ocr = OCR()
            result = ocr.get_captcha(temp_file.name)
        else:
            task = self.im.createCaptchaTask(img, imgtype, temp_file.name, self.__name__, result_type)
            self.task = task

            while task.isWaiting():
                if self.abort():
                    self.im.removeTask(task)
                    raise Abort
                sleep(1)

            #TODO task handling
            self.im.removeTask(task)

            if task.error and has_plugin: #ignore default error message since the user could use OCR
                self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
            elif task.error:
                self.fail(task.error)
            elif not task.result:
                self.fail(_("No captcha result obtained in appropriate time."))

            result = task.result
            self.log.debug("Received captcha result: %s" % str(result))

        if not self.core.debug:
            try:
                remove(temp_file.name)
            except Exception:
                pass

        return result

    def fail(self, reason):
        """ fail and give reason """
        raise Fail(reason)
