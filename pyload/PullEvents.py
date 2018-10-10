# -*- coding: utf-8 -*-
# @author: mkaay


from builtins import object
from time import time

from pyload.utils import uniqify


class PullManager(object):
    def __init__(self, core):
        self.core = core
        self.clients = []

    def newClient(self, uuid):
        self.clients.append(Client(uuid))

    def clean(self):
        for n, client in enumerate(self.clients):
            if client.lastActive + 30 < time():
                del self.clients[n]

    def getEvents(self, uuid):
        events = []
        validUuid = False
        for client in self.clients:
            if client.uuid == uuid:
                client.lastActive = time()
                validUuid = True
                while client.newEvents():
                    events.append(client.popEvent().toList())
                break
        if not validUuid:
            self.newClient(uuid)
            events = [
                ReloadAllEvent("queue").toList(),
                ReloadAllEvent("collector").toList()]
        return uniqify(events, repr)

    def addEvent(self, event):
        for client in self.clients:
            client.addEvent(event)


class Client(object):
    def __init__(self, uuid):
        self.uuid = uuid
        self.lastActive = time()
        self.events = []

    def newEvents(self):
        return len(self.events) > 0

    def popEvent(self):
        if not len(self.events):
            return None
        return self.events.pop(0)

    def addEvent(self, event):
        self.events.append(event)


class UpdateEvent(object):
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination

    def toList(self):
        return ["update", self.destination, self.type, self.id]


class RemoveEvent(object):
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination

    def toList(self):
        return ["remove", self.destination, self.type, self.id]


class InsertEvent(object):
    def __init__(self, itype, iid, after, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.after = after
        self.destination = destination

    def toList(self):
        return ["insert", self.destination, self.type, self.id, self.after]


class ReloadAllEvent(object):
    def __init__(self, destination):
        assert destination == "queue" or destination == "collector"
        self.destination = destination

    def toList(self):
        return ["reload", self.destination]


class AccountUpdateEvent(object):
    def toList(self):
        return ["account"]


class ConfigUpdateEvent(object):
    def toList(self):
        return ["config"]
