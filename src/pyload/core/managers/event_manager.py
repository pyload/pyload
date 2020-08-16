# -*- coding: utf-8 -*-

import time

from ..utils.purge import uniquify


class EventManager:
    def __init__(self, core):
        self.pyload = core
        self._ = core._
        self.clients = []

    def new_client(self, uuid):
        self.clients.append(Client(uuid))

    def clean(self):
        for n, client in enumerate(self.clients):
            if client.last_active + 30 < time.time():
                del self.clients[n]

    def get_events(self, uuid):
        events = []
        valid_uuid = False
        for client in self.clients:
            if client.uuid == uuid:
                client.last_active = time.time()
                valid_uuid = True
                while client.new_events():
                    events.append(client.pop_event().to_list())
                break
        if not valid_uuid:
            self.new_client(uuid)
            events = [
                ReloadAllEvent("queue").to_list(),
                ReloadAllEvent("collector").to_list(),
            ]
        return uniquify(events)  # return uniquify(events, repr)

    def add_event(self, event):
        for client in self.clients:
            client.add_event(event)


class Client:
    def __init__(self, uuid):
        self.uuid = uuid
        self.last_active = time.time()
        self.events = []

    def new_events(self):
        return len(self.events) > 0

    def pop_event(self):
        if not len(self.events):
            return None
        return self.events.pop(0)

    def add_event(self, event):
        self.events.append(event)


class UpdateEvent:
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination

    def to_list(self):
        return ["update", self.destination, self.type, self.id]


class RemoveEvent:
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination

    def to_list(self):
        return ["remove", self.destination, self.type, self.id]


class InsertEvent:
    def __init__(self, itype, iid, after, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.after = after
        self.destination = destination

    def to_list(self):
        return ["insert", self.destination, self.type, self.id, self.after]


class ReloadAllEvent:
    def __init__(self, destination):
        assert destination == "queue" or destination == "collector"
        self.destination = destination

    def to_list(self):
        return ["reload", self.destination]


class AccountUpdateEvent:
    def to_list(self):
        return ["account"]


class ConfigUpdateEvent:
    def to_list(self):
        return ["config"]
