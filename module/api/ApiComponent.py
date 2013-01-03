#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.remote.ttypes import Iface

# Workaround to let code-completion think, this is subclass of Iface
Iface = object
class ApiComponent(Iface):

    def __init__(self, core):
        # Only for auto completion, this class can not be instantiated
        from pyload import Core
        assert isinstance(core, Core)
        assert issubclass(ApiComponent, Iface)
        self.core = core
        # No instantiating!
        raise Exception()