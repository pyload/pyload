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
        self.prgr = {}
        self.result = ()
        self.errresult = ()
    
    def addCallback(self, f, *cargs, **ckwargs):
        self.call.append((f, cargs, ckwargs))
        if self.result:
            args, kwargs = self.result
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)
    
    #test not in use
    def addProgress(self, chain, f):
        if self.prgr.has_key(chain):
            self.prgr[chain].append(f)
        else:
            self.prgr[chain] = [f]
    
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
    
    #test not in use
    def progress(self, chain, *args, **kwargs):
        if not self.prgr.has_key(chain):
            return
        for f in self.prgr[chain]:
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
        
        def __init__(self, d):
            self.d = d
        
        def wait(self):
            self.d.addCallback(self.callb)
            self.d.addErrback(self.errb)
            while self.waiting:
                sleep(0.5)
            if self.err:
                if issubclass(self.err[0][0], Exception):
                    raise self.err[0][0]()
                raise Exception(self.err)
            return self.args
        
        def callb(self, *args, **kwargs):
            self.waiting = False
            self.args = (args, kwargs)
        
        def errb(self, *args, **kwargs):
            self.waiting = False
            self.err = (args, kwargs)
    w = Waiter(d)
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

class WrappedDeferred(object):
    def __init__(self, download, d):
        self.__dict__["download"] = download
        self.__dict__["d"] = d
    
    def addCallback(self, *args, **kwargs):
        self.__dict__["d"].addCallback(*args, **kwargs)
    
    def addErrback(self, *args, **kwargs):
        self.__dict__["d"].addErrback(*args, **kwargs)
    
    def callback(self, *args, **kwargs):
        self.__dict__["d"].callback(*args, **kwargs)
    
    def error(self, *args, **kwargs):
        self.__dict__["d"].error(*args, **kwargs)
    
    def __getattr__(self, attr):
        return getattr(self.download, attr)
    
    def __setattr__(self, attr, val):
        return setattr(self.download, attr, val)
