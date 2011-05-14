# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""

from time import time
from module.utils import uniqify

class PullManager():
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
            events = [ReloadAllEvent("queue").toList(), ReloadAllEvent("collector").toList()]
        return uniqify(events, repr)
    
    def addEvent(self, event):
        for client in self.clients:
            client.addEvent(event)

class Client():
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

class UpdateEvent():
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination
    
    def toList(self):
        return ["update", self.destination, self.type, self.id]

class RemoveEvent():
    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination
    
    def toList(self):
        return ["remove", self.destination, self.type, self.id]

class InsertEvent():
    def __init__(self, itype, iid, after, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.after = after
        self.destination = destination
    
    def toList(self):
        return ["insert", self.destination, self.type, self.id, self.after]

class ReloadAllEvent():
    def __init__(self, destination):
        assert destination == "queue" or destination == "collector"
        self.destination = destination
        
    def toList(self):
        return ["reload", self.destination]

class AccountUpdateEvent():
    def toList(self):
        return ["account"]

class ConfigUpdateEvent():
    def toList(self):
        return ["config"]
