#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ApiComponent:

    def __init__(self, core):
        # Only for auto completion, this class can not be instantiated
        from pyload import Core
        assert isinstance(core, Core)
        self.core = core
        # No instantiating!
        raise Exception()