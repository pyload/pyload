#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.remote.ttypes import Iface

# Workaround to let code-completion think, this is subclass of Iface
Iface = object
class ApiComponent(Iface):

    __slots__ = []

    def __init__(self, core, user):
        # Only for auto completion, this class can not be instantiated
        from pyload import Core
        from module.datatypes.User import User
        assert isinstance(core, Core)
        assert issubclass(ApiComponent, Iface)
        self.core = core
        assert isinstance(user, User)
        self.user = user
        # No instantiating!
        raise Exception()