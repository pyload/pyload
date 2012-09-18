# -*- coding: utf-8 -*-

from threading import Lock
from traceback import print_exc
from time import time

from module.utils import lock

class EventManager:
    """
    Handles all event-related tasks, also stores an event queue for clients, so they can retrieve them later.

    **Known Events:**
    Most addon methods exist as events. These are some additional known events.

    ===================== ================ ===========================================================
    Name                      Arguments      Description
    ===================== ================ ===========================================================
    metaEvent             eventName, *args Called for every event, with eventName and original args
    downloadPreparing     fid              A download was just queued and will be prepared now.
    downloadStarts        fid              A plugin will immediately start the download afterwards.
    linksAdded            links, pid       Someone just added links, you are able to modify these links.
    allDownloadsProcessed                  All links were handled, pyLoad would idle afterwards.
    allDownloadsFinished                   All downloads in the queue are finished.
    unrarFinished         folder, fname    An Unrar job finished
    configChanged         sec, opt, value  The config was changed.
    ===================== ================ ===========================================================

    | Notes:
    |    allDownloadsProcessed is *always* called before allDownloadsFinished.
    |    configChanged is *always* called before pluginConfigChanged.
    """

    CLIENT_EVENTS = ("packageUpdated", "packageInserted", "linkUpdated", "packageDeleted")

    def __init__(self, core):
        self.core = core
        self.log = core.log

        # uuid : list of events
        self.clients = {}
        self.events = {"metaEvent": []}

        self.lock = Lock()

    def getEvents(self, uuid):
        """ Get accumulated events for uuid since last call, this also registers a new client """
        if uuid not in self.clients:
            self.clients[uuid] = Client()
        return self.clients[uuid].get()

    def addEvent(self, event, func):
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

    def dispatchEvent(self, event, *args):
        """dispatches event with args"""
        for f in self.events["metaEvent"]:
            try:
                f(event, *args)
            except Exception, e:
                self.log.warning("Error calling event handler %s: %s, %s, %s"
                % ("metaEvent", f, args, str(e)))
                if self.core.debug:
                    print_exc()

        if event in self.events:
            for f in self.events[event]:
                try:
                    f(*args)
                except Exception, e:
                    self.log.warning("Error calling event handler %s: %s, %s, %s"
                    % (event, f, args, str(e)))
                    if self.core.debug:
                        print_exc()

        self.updateClients(event, args)

    @lock
    def updateClients(self, event, args):
        # append to client event queue
        if event in self.CLIENT_EVENTS:
            for uuid, client in self.clients.items():
                if client.delete():
                    del self.clients[uuid]
                else:
                    client.append(event, args)

    def removeFromEvents(self, func):
        """ Removes func from all known events """
        for name, events in self.events.iteritems():
            if func in events:
                events.remove(func)



class Client:

    # delete clients after this time
    TIMEOUT = 60 * 60
    # max events, if this value is reached you should assume that older events were dropped
    MAX = 30

    def __init__(self):
        self.lastActive = time()
        self.events = []

    def delete(self):
        return self.lastActive + self.TIMEOUT < time()

    def append(self, event, args):
        ev = (event, args)
        if ev not in self.events:
            self.events.insert(0, ev)

        del self.events[self.MAX:]


    def get(self):
        self.lastActive = time()

        events = self.events
        self.events = []

        return [(ev, [str(x) for x in args]) for ev, args in events]