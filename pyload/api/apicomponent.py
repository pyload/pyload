# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.remote.apitypes import Iface

# Workaround to let code-completion think, this is subclass of Iface
Iface = object


class ApiComponent(Iface):

    __slots__ = []

    def __init__(self, core, user):
        # Only for auto completion, this class can not be instantiated
        from pyload import Core
        from pyload.datatypes.User import User
        assert isinstance(core, Core)
        assert issubclass(ApiComponent, Iface)
        self.core = core
        assert isinstance(user, User)
        self.user = user
        self.primaryUID = 0
        # No instantiating!
        raise Exception
