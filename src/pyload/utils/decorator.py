# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import str
from multiprocessing import Process

from future import standard_library

from .layer.safethreading import Thread

standard_library.install_aliases()


# def deprecated(by=None):
# new_func = by
# def wrapper(old_func):
# def new(self, *args, **kargs):
# if new_func:
# self.pyload.log.debug("`{0}` has been deprecated, use `{1}` instead".format(
# old_func.__name__, new_func.__name__))
# return new_func(self, *args, **kargs)
# else:
# self.pyload.log.error(_("`{0}` has been removed").format(old_func.__name__))
# print_traceback()
# return new
# return wrapper


def fork(daemon=True):
    def wrapper(func):
        def new(self, *args, **kwargs):
            p = Process(target=func, args=args, kwargs=kwargs)
            p.daemon = bool(daemon)
            p.start()
            return p
        return new
    return wrapper


# NOTE: Don't use this if you can use the metaclass struct.abc.Singleton
def singleton(klass):
    inst = {}

    def get_inst(*args, **kwargs):
        if klass not in inst:
            inst[klass] = klass(*args, **kwargs)
        return inst[klass]

    return get_inst


def threaded(daemon=True):
    def wrapper(func):
        def new(self, *args, **kwargs):
            thread = Thread(target=func, args=args, kwargs=kwargs)
            thread.setDaemon(daemon)
            thread.start()
            return thread
        return new
    return wrapper


def trycatch(callback):
    """
    Decorator that executes the function and returns the value or fallback on any exception.
    """
    from .debug import print_traceback

    def wrapper(func):
        def new(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                msg = "Error executing `{0}` | {1}".format(
                    func.__name__, str(e))
                self.pyload.log.debug(msg)
                if self.pyload.debug:
                    print_traceback()
                return callback(e)
        return new
    return wrapper
