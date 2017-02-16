# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from multiprocessing import Process

from pyload.utils.check import isiterable
from pyload.utils.lib.threading import Thread


# def deprecated(by=None):
# new_func = by
# def wrapper(old_func):
# def new(self, *args, **kargs):
# if new_func:
# self.pyload.log.debug('`{}` has been deprecated, use `{}` instead'.format(
# old_func.__name__, new_func.__name__))
# return new_func(self, *args, **kargs)
# else:
# self.pyload.log.error(_('`{}` has been removed').format(old_func.__name__))
# print_traceback()
# return new
# return wrapper


def fork(func, daemon=True):
    def new(self, *args, **kwargs):
        p = Process(target=func, args=args, kwargs=kwargs)
        p.daemon = bool(daemon)
        p.start()
        return p
    return new


def iterate(func):
    def new(value, *args, **kwargs):
        values = value if isiterable(value) else (value,)
        for v in values:
            yield func(v, *args, **kwargs)
    return new


def readlock(func):
    def new(self, *args, **kwargs):
        args.lock.acquire(shared=True)
        try:
            return func(*args, **kwargs)
        finally:
            args.lock.release()

    return new


def lock(func):
    def new(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return new


def threaded(func, daemon=True):
    def new(self, *args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.setDaemon(daemon)
        t.start()
        return t
    return new


def trycatch(callback):
    """
    Decorator that executes the function and returns the value or fallback on any exception.
    """
    from pyload.utils.debug import print_traceback

    def wrapper(func):
        def new(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                msg = 'Error executing `{}` | {}'.format(
                    func.__name__, e.message)
                self.pyload.log.debug(msg)
                if self.pyload.debug:
                    print_traceback()
                return callback(e)
        return new
    return wrapper
