# -*- coding: utf-8 -*-


from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.core.manager.base import BaseManager

standard_library.install_aliases()


class EventManager(BaseManager):
    """Handles all event-related tasks, also stores an event queue for clients,
    so they can retrieve them later.

    **Known Events:**
    Most addon methods exist as events. These are some additional known events.

    ===================== ================ ====================================
    Name                      Arguments      Description
    ===================== ================ ====================================
    event                 event_name, args Called for every event,
                                           with event_name and original args
    download:preparing    fid              A download was just queued and
                                           will be prepared now.
    download:start        fid              A plugin will immediately start
                                           the download afterwards.
    download:allProcessed                  All links were handled,
                                           pyLoad would idle afterwards.
    download:allFinished                   All downloads in the queue are
                                           finished.
    config:changed        sec, opt, value  The config was changed.
    ===================== ================ ====================================

    | Notes:
    |    download:allProcessed is *always* called before download:allFinished

    """

    def setup(self):
        self.events = {'event': []}

    def listen_to(self, event, func):
        """Adds an event listener for event name."""
        if event in self.events:
            if func in self.events[event]:
                self.pyload.log.debug(
                    'Function already registered {0}'.format(func))
            else:
                self.events[event].append(func)
        else:
            self.events[event] = [func]

    def remove_event(self, event, func):
        """Removes previously added event listener."""
        if event in self.events:
            self.events[event].remove(func)

    def remove_from_events(self, func):
        """Removes func from all known events."""
        for name, events in self.events.items():
            if func in events:
                events.remove(func)

    def fire(self, event, *args, **kwargs):
        """Dispatches event with args."""
        # dispatch the meta event
        if event != 'event':
            self.pyload.log.debug(event)
            self.fire('event', *(event,) + args, **kwargs)

        if event in self.events:
            for func in self.events[event]:
                try:
                    func(*args, **kwargs)
                except Exception as exc:
                    self.pyload.log.warning(
                        'Error calling event handler '
                        '{0}: {1}, {2}'.format(event, func, args))
                    self.pyload.log.error(exc, exc_info=self.pyload.debug)
