# -*- coding: utf-8 -*-

from module.plugins.internal.Plugin import Plugin


class Expose(object):
    """
    Used for decoration to declare rpc services
    """
    def __new__(cls, f, *args, **kwargs):
        hookManager.addRPC(f.__module__, f.func_name, f.func_doc)
        return f


def threaded(fn):

    def run(*args, **kwargs):
        hookManager.startThread(fn, *args, **kwargs)

    return run


class Addon(Plugin):
    __name__    = "Addon"
    __type__    = "hook"  #@TODO: Change to `addon` in 0.4.10
    __version__ = "0.13"
    __status__  = "testing"

    __threaded__ = []  #@TODO: Remove in 0.4.10

    __description__ = """Base addon plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PERIODICAL_INTERVAL = None


    def __init__(self, core, manager):
        self._init(core)

        #: `HookManager`
        self.manager = manager

        #: Automatically register event listeners for functions, attribute will be deleted dont use it yourself
        self.event_map = {}

        #: Deprecated alternative to event_map
        #: List of events the plugin can handle, name the functions exactly like eventname.
        self.event_list = []  #@NOTE: dont make duplicate entries in event_map

        self.info['ip'] = None  #@TODO: Remove in 0.4.10

        #: Callback of periodical job task, used by HookManager
        self.cb       = None
        self.interval = self.PERIODICAL_INTERVAL

        self.init()
        self.init_events()


    def init_events(self):
        if self.event_map:
            for event, funcs in self.event_map.items():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.manager.addEvent(event, getattr(self, f))
                else:
                    self.manager.addEvent(event, getattr(self, funcs))

            #: Delete for various reasons
            self.event_map = None

        if self.event_list:
            self.log_debug("Deprecated method `event_list`, use `event_map` instead")

            for f in self.event_list:
                self.manager.addEvent(f, getattr(self, f))

            self.event_list = None


    def set_interval(self, value):
        newinterval = max(0, self.PERIODICAL_INTERVAL, value)

        if newinterval != value:
            return False

        if newinterval != self.interval:
            self.interval = newinterval

        return True


    def start_periodical(self, interval=None, threaded=False, delay=None):
        if interval is not None and self.set_interval(interval) is False:
            return False
        else:
            self.cb = self.pyload.scheduler.addJob(max(1, delay), self._periodical, [threaded], threaded=threaded)
            return True


    def restart_periodical(self, *args, **kwargs):
        self.stop_periodical()
        return self.start_periodical(*args, **kwargs)


    def stop_periodical(self):
        try:
            return self.pyload.scheduler.removeJob(self.cb)
        finally:
            self.cb = None


    def _periodical(self, threaded):
        try:
            self.periodical()

        except Exception, e:
            self.log_error(_("Error executing periodical task: %s") % e, trace=True)

        self.restart_periodical(threaded=threaded, delay=self.interval)


    def periodical(self):
        raise NotImplementedError


    def save_info(self):
        self.store("info", self.info)


    def restore_info(self):
        self.retrieve("info", self.info)


    @property
    def activated(self):
        """
        Checks if addon is activated
        """
        return self.get_config("activated")


    #: Deprecated method, use `activated` property instead (Remove in 0.4.10)
    def isActivated(self, *args, **kwargs):
        return self.activated


    def deactivate(self):
        """
        Called when addon was deactivated
        """
        pass


    #: Deprecated method, use `deactivate` instead (Remove in 0.4.10)
    def unload(self, *args, **kwargs):
        self.save_info()
        return self.deactivate(*args, **kwargs)


    def activate(self):
        """
        Called when addon was activated
        """
        pass


    #: Deprecated method, use `activate` instead (Remove in 0.4.10)
    def coreReady(self, *args, **kwargs):
        self.restore_info()
        return self.activate(*args, **kwargs)


    def exit(self):
        """
        Called by core.shutdown just before pyLoad exit
        """
        pass


    #: Deprecated method, use `exit` instead (Remove in 0.4.10)
    def coreExiting(self, *args, **kwargs):
        self.unload(*args, **kwargs)  #@TODO: Fix in 0.4.10
        return self.exit(*args, **kwargs)


    def download_preparing(self, pyfile):
        pass


    #: Deprecated method, use `download_preparing` instead (Remove in 0.4.10)
    def downloadPreparing(self, pyfile):
        if pyfile.plugin.req is not None:  #@TODO: Remove in 0.4.10
            return self.download_preparing(pyfile)


    def download_finished(self, pyfile):
        pass


    #: Deprecated method, use `download_finished` instead (Remove in 0.4.10)
    def downloadFinished(self, *args, **kwargs):
        return self.download_finished(*args, **kwargs)


    def download_failed(self, pyfile):
        pass


    #: Deprecated method, use `download_failed` instead (Remove in 0.4.10)
    def downloadFailed(self, *args, **kwargs):
        return self.download_failed(*args, **kwargs)


    def package_finished(self, pypack):
        pass


    #: Deprecated method, use `package_finished` instead (Remove in 0.4.10)
    def packageFinished(self, *args, **kwargs):
        return self.package_finished(*args, **kwargs)


    def before_reconnect(self, ip):
        pass


    #: Deprecated method, use `before_reconnect` instead (Remove in 0.4.10)
    def beforeReconnecting(self, *args, **kwargs):
        return self.before_reconnect(*args, **kwargs)


    def after_reconnect(self, ip, oldip):
        pass


    #: Deprecated method, use `after_reconnect` instead (Remove in 0.4.10)
    def afterReconnecting(self, ip):
        self.after_reconnect(ip, self.info['ip'])
        self.info['ip'] = ip


    def captcha_task(self, task):
        """
        New captcha task for the plugin, it MUST set the handler and timeout or will be ignored
        """
        pass


    #: Deprecated method, use `captcha_task` instead (Remove in 0.4.10)
    def newCaptchaTask(self, *args, **kwargs):
        return self.captcha_task(*args, **kwargs)


    def captcha_correct(self, task):
        pass


    #: Deprecated method, use `captcha_correct` instead (Remove in 0.4.10)
    def captchaCorrect(self, *args, **kwargs):
        return self.captcha_correct(*args, **kwargs)


    def captcha_invalid(self, task):
        pass


    #: Deprecated method, use `captcha_invalid` instead (Remove in 0.4.10)
    def captchaInvalid(self, *args, **kwargs):
        return self.captcha_invalid(*args, **kwargs)
