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
