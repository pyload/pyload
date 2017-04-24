# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from builtins import str
from multiprocessing import Process

from future import standard_library
standard_library.install_aliases()

from .check import isiterable
from .layer.safethreading import Thread


__all__ = [
    'fork',
    'iterate',
    'lock',
    'readlock',
    'singleton',
    'threaded',
    'trycatch']


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


def fork(func, daemon=True):
    def new(self, *args, **kwargs):
        proc = Process(target=func, args=args, kwargs=kwargs)
        proc.daemon = bool(daemon)
        proc.start()
        return proc
    return new


def iterate(func):
    def new(seq, *args, **kwargs):
        if isiterable(seq):
            return type(seq)(func(val, *args, **kwargs) for val in seq)
        return func(seq, *args, **kwargs)
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


# NOTE: Don't use this if you can use the metaclass struct.abc.Singleton
def singleton(klass):
    inst = {}

    def get_inst(*args, **kwargs):
        if klass not in inst:
            inst[klass] = klass(*args, **kwargs)
        return inst[klass]
    return get_inst


def threaded(func, daemon=True):
    def new(self, *args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.setDaemon(daemon)
        thread.start()
        return thread
    return new


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
