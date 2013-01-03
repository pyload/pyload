#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, RequirePerm, Permission

from ApiComponent import ApiComponent

class CollectorApi(ApiComponent):
    """ Link collector """

    @RequirePerm(Permission.All)
    def getCollector(self):
        pass

    @RequirePerm(Permission.Add)
    def addToCollector(self, links):
        pass

    @RequirePerm(Permission.Add)
    def addFromCollector(self, name, new_name):
        pass

    @RequirePerm(Permission.Delete)
    def deleteCollPack(self, name):
        pass

    @RequirePerm(Permission.Add)
    def renameCollPack(self, name, new_name):
        pass

    @RequirePerm(Permission.Delete)
    def deleteCollLink(self, url):
        pass


if Api.extend(CollectorApi):
    del CollectorApi