from threading import Thread
from time import time, sleep

def inttime():
    return int(time())

class AlreadyCalled(Exception):
    pass

def callInThread(f, *args, **kwargs):
    class FThread(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.setDaemon(True)
            self.d = Deferred()
        def run(self):
            ret = f(*args, **kwargs)
            self.d.callback(ret)
    t = FThread()
    t.start()
    return t.d

class Deferred():
    def __init__(self):
        self.call = []
        self.err = []
        self.result = ()
        self.errresult = ()
    
    def addCallback(self, f, *cargs, **ckwargs):
        self.call.append((f, cargs, ckwargs))
        if self.result:
            args, kwargs = self.result
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)
    
    def addErrback(self, f, *cargs, **ckwargs):
        self.err.append((f, cargs, ckwargs))
        if self.errresult:
            args, kwargs = self.errresult
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)
    
    def callback(self, *args, **kwargs):
        if self.result:
            raise AlreadyCalled
        self.result = (args, kwargs)
        for f, cargs, ckwargs in self.call:
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)
    
    def error(self, *args, **kwargs):
        self.errresult = (args, kwargs)
        for f, cargs, ckwargs in self.err:
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)

#decorator
def threaded(f):
    def ret(*args, **kwargs):
        return callInThread(f, *args, **kwargs)
    return ret

def waitFor(d):
    class Waiter():
        waiting = True
        args = ()
        err = None
        
        def wait(self):
            d.addCallback(self.callb)
            d.addErrback(self.errb)
            while self.waiting:
                sleep(0.5)
            if self.err:
                raise Exception(self.err)
            return self.args
        
        def callb(self, *args, **kwargs):
            self.waiting = False
            self.args = (args, kwargs)
        
        def errb(self, *args, **kwargs):
            self.waiting = False
            self.err = (args, kwargs)
    w = Waiter()
    return w.wait()

class DeferredGroup(Deferred):
    def __init__(self, group=[]):
        Deferred.__init__(self)
        self.group = group
        self.done = 0
        
        for d in self.group:
            d.addCallback(self._cb)
            d.addErrback(self.error)
    
    def addDeferred(self, d):
        d.addCallback(self._cb)
        d.addErrback(self.error)
        self.group.append(d)
    
    def _cb(self, *args, **kwargs):
        self.done += 1
        if len(self.group) == self.done:
            self.callback()

class WrappedDeferred():
    def __init__(self, download, d):
        self.download = download
        self.d = d
    
    def addCallback(self, *args, **kwargs):
        self.d.addCallback(*args, **kwargs)
    
    def addErrback(self, *args, **kwargs):
        self.d.addErrback(*args, **kwargs)
    
    def __getattr__(self, attr):
        return getattr(self.download, attr)
