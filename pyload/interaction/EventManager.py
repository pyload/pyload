# -*- coding: utf-8 -*-

from threading import Lock
from traceback import print_exc


class EventManager:
    """
    Handles all event-related tasks, also stores an event queue for clients, so they can retrieve them later.

    **Known Events:**
    Most addon methods exist as events. These are some additional known events.

    ======================= ======================== ==========================================================
    Name                    Arguments                Description
    ======================= ======================== ==========================================================
    event                   eventName, *args         Called for every event, with eventName and original args
    download:preparing      pyfile                   A download was just queued and will be prepared now
    download:start          pyfile, url, filename    A plugin will immediately start the download afterwards
    download:finished       pyfile                   Fired when a download is completed
    download:failed         pyfile                   Fired when downloading fails
    download:allProcessed                            All links were handled, pyLoad would idle afterwards
    download:allFinished                             All downloads in the queue are finished.
    package:finished        pypack                   Fired when a package is completed
    reconnect:before        ip                       Fired before trying to change IP address
    reconnect:after         ip, oldip                Fired after succesfully changed IP address
    reconnect:failed        ip                       Fired if fails to got a new IP
    config:changed          section, option, value   The config was changed.
    ======================= ======================== ==========================================================

    | Notes:
    |    download:allProcessed is *always* called before download:allFinished.
    """

    def __init__(self, core):
        self.core = core
        self.log = core.log

        self.events = {"event": []}

        self.lock = Lock()

    def listenTo(self, event, func):
        """Adds an event listener for event name"""
        if event in self.events:
            if func in self.events[event]:
                self.log.debug("Function already registered %s" % func)
            else:
                self.events[event].append(func)
        else:
            self.events[event] = [func]

    def removeEvent(self, event, func):
        """removes previously added event listener"""
        if event in self.events:
            self.events[event].remove(func)

    def removeFromEvents(self, func):
        """ Removes func from all known events """
        for name, events in self.events.iteritems():
            if func in events:
                events.remove(func)

    def dispatchEvent(self, event, *args, **kwargs):
        """dispatches event with args"""
        # dispatch the meta event
        if event != "event":
            self.dispatchEvent("event", *(event,) + args, **kwargs)

        if event in self.events:
            for f in self.events[event]:
                try:
                    f(*args, **kwargs)
                except Exception, e:
                    self.log.warning("Error calling event handler %s: %s, %s, %s"
                                     % (event, f, args, str(e)))
                    self.core.print_exc()