# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

from __future__ import absolute_import, unicode_literals

import os
import random
import time
from builtins import object

from future import standard_library

from pyload.utils.convert import to_str
from pyload.utils.fs import lopen, makedirs, remove

standard_library.install_aliases()


# TODO
#   more attributes if needed
#   get rid of catpcha & container plugins ?! (move to crypter & internals)
#   adapt old plugins as needed
class Fail(Exception):
    """
    Raised when failed.
    """
    __slots__ = []


class Retry(Exception):
    """
    Raised when start again from beginning.
    """
    __slots__ = []


class Abort(Exception):
    """
    Raised when aborted.
    """
    __slots__ = []


class Base(object):
    """
    The Base plugin class with all shared methods and every possible attribute for plugin definition.
    """
    # Version as string or number
    __version__ = "0.1"
    # Type of the plugin, will be inherited and should not be set!
    __type__ = ""
    # Regexp pattern which will be matched for download/crypter plugins
    __pattern__ = r''
    # Internal addon plugin which is always loaded
    __internal__ = False
    # When True this addon can be enabled by every user
    __user_context__ = False
    # Config definition: list of  (name, type, label, default) or
    # (name, label, desc, Input(...))
    __config__ = tuple()
    # Short description, one liner
    __description__ = ""
    # More detailed text
    __explanation__ = """"""
    # List of needed modules
    __dependencies__ = tuple()
    # Used to assign a category for addon plugins
    __category__ = ""
    # Tags to categorize the plugin, see documentation for further info
    __tags__ = tuple()
    # Base64 encoded .png icon, should be 32x32, please do not use sizes above
    # ~2KB, for bigger icons use url.
    __icon__ = ""
    # Alternative, link to png icon
    __icon_url__ = ""
    # Domain name of the service
    __domain__ = ""
    # Url with general information/support/discussion
    __url__ = ""
    # Url to term of content, user is accepting these when using the plugin
    __toc_url__ = ""
    # Url to service (to buy premium) for accounts
    __ref_url__ = ""

    __author__ = tuple()
    __author_mail__ = tuple()

    def __init__(self, core, owner=None):
        self.__name__ = self.__class__.__name__

        # Core instance
        self.__pyload = core
        self._ = core._

        if owner is not None:
            # :class:`Api`, user api when user is set
            self.api = self.pyload_core.api.with_user_context(owner)
            if not self.api:
                raise Exception("Plugin running with invalid user")

            # :class:`User`, user related to this plugin
            self.owner = self.api.user
        else:
            self.api = self.pyload_core.api
            self.owner = None

        # last interaction task
        self.task = None

    def __getitem__(self, item):
        """
        Retrieves meta data attribute.
        """
        return getattr(self, "__{0}__".format(item))

    @property
    def pyload_core(self):
        return self.__pyload

    def log_info(self, *args, **kwargs):
        """
        Print args to log at specific level

        :param args: Arbitrary object which should be logged
        :param kwargs: sep=(how to separate arguments), default = " | "
        """
        self._log("info", *args, **kwargs)

    def log_warning(self, *args, **kwargs):
        self._log("warning", *args, **kwargs)

    def log_error(self, *args, **kwargs):
        self._log("error", *args, **kwargs)

    def log_debug(self, *args, **kwargs):
        self._log("debug", *args, **kwargs)

    def _log(self, level, *args, **kwargs):
        if "sep" in kwargs:
            sep = "{0}".format(kwargs['sep'])
        else:
            sep = " | "

        strings = []
        for obj in args:
            strings.append(to_str(obj, obj))

        getattr(self.log, level)("{0}: {1}".format(
            self.__name__, sep.join(strings)))

    def get_name(self):
        """
        Name of the plugin class.
        """
        return self.__name__

    @property
    def pattern(self):
        """
        Gives the compiled pattern of the plugin.
        """
        return self.pyload_core.pgm.get_plugin(self.__type__, self.__name__).re

    def set_config(self, option, value):
        """
        Set config value for current plugin.
        """
        self.pyload_core.config.set(self.__name__, option, value)

    # TODO: Recheck...
    def get_config(self, option):
        """
        Returns config value for current plugin.
        """
        return self.pyload_core.config.get(self.__name__, option)

    def set_storage(self, key, value):
        """
        Saves a value persistently to the database.
        """
        self.pyload_core.db.set_storage(self.__name__, key, value)

    def store(self, key, value):
        """
        Same as `set_storage`.
        """
        self.pyload_core.db.set_storage(self.__name__, key, value)

    def get_storage(self, key=None, default=None):
        """
        Retrieves saved value or dict of all saved entries if key is None.
        """
        if key is not None:
            return self.pyload_core.db.get_storage(self.__name__, key) or default
        return self.pyload_core.db.get_storage(self.__name__, key)

    def retrieve(self, *args, **kwargs):
        """
        Same as `get_storage`.
        """
        return self.get_storage(*args, **kwargs)

    def del_storage(self, key):
        """
        Delete entry in db.
        """
        self.pyload_core.db.del_storage(self.__name__, key)

    def abort(self):
        """
        Check if plugin is in an abort state, is overwritten by subtypes.
        """
        return False

    def check_abort(self):
        """
        Will be overwritten to determine if control flow should be aborted.
        """
        if self.abort():
            raise Abort

    def load(self, url, get={}, post={}, ref=True,
             cookies=True, just_header=False, decode=False):
        """
        Load content at url and returns it

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
            raise Exception("Plugin type does not have Request attribute")
        self.check_abort()

        res = self.req.load(url, get, post, ref, cookies,
                            just_header, decode=decode)

        if self.pyload_core.debug:
            from inspect import currentframe

            frame = currentframe()
            dumpdir = os.path.join(self.pyload_core.cachedir,
                                   'plugins', self.__name__)
            makedirs(dumpdir, exist_ok=True)

            filepath = os.path.join(dumpdir, "dump_{0}_line{1}.html".format(
                frame.f_back.f_code.co_name, frame.f_back.f_lineno))
            with lopen(filepath, mode='wb') as fp:
                fp.write(res)
            del frame  # delete the frame or it wont be cleaned

        if just_header:
            # parse header
            header = {'code': self.req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

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

    def invalid_task(self):
        if self.task:
            self.task.invalid()

    def invalid_captcha(self):
        self.log_debug("Deprecated method .invalid_captcha, use .invalid_task")
        self.invalid_task()

    def correct_task(self):
        if self.task:
            self.task.correct()

    def correct_captcha(self):
        self.log_debug("Deprecated method .correct_captcha, use .correct_task")
        self.correct_task()

    def decrypt_captcha(
            self, url, get={},
            post={},
            cookies=True, forceuser=False, imgtype='jpg',
            result_type='textual'):
        """
        Loads a captcha and decrypts it with ocr, plugin, user input

        :param url: url of captcha image
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param forceuser: if True, ocr is not used
        :param imgtype: Type of the Image
        :param result_type: 'textual' if text is written on the captcha
        or 'positional' for captcha where the user have to click
        on a specific region on the captcha

        :return: result of decrypting
        """
        img = self.load(url, get=get, post=post, cookies=cookies)

        id = "{0:.2f}".format(time.time())[-6:].replace(".", "")
        with lopen(os.path.join("tmp_captcha_{0}_{1}.{2}".format(self.__name__, id, imgtype)), mode='wb') as fp:
            fp.write(img)

            name = "{0}OCR".format(self.__name__)
            has_plugin = name in self.pyload_core.pgm.get_plugins("internal")

            if self.pyload_core.captcha:
                OCR = self.pyload_core.pgm.load_class("internal", name)
            else:
                OCR = None

            if OCR and not forceuser:
                time.sleep(random.randint(3000, 5000) // 1000)
                self.check_abort()

                ocr = OCR()
                result = ocr.get_captcha(fp.name)
            else:
                task = self.pyload_core.exm.create_captcha_task(
                    img, imgtype, fp.name, self.__name__, result_type)
                self.task = task

                while task.is_waiting():
                    if self.abort():
                        self.pyload_core.exm.remove_task(task)
                        raise Abort
                    time.sleep(1)

                # TODO: task handling
                self.pyload_core.exm.remove_task(task)

                if task.error and has_plugin:  # ignore default error message since the user could use OCR
                    self.fail(
                        self._(
                            "Pil and tesseract not installed and no Client connected for captcha decrypting"))
                elif task.error:
                    self.fail(task.error)
                elif not task.result:
                    self.fail(
                        self._(
                            "No captcha result obtained in appropriate time"))

                result = task.result
                self.pyload_core.log.debug(
                    "Received captcha result: {0}".format(result))

            if not self.pyload_core.debug:
                try:
                    remove(fp.name)
                except Exception:
                    pass

        return result

    def fail(self, reason):
        """
        Fail and give reason.
        """
        raise Fail(reason)
