# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from pyload.remote.apitypes import Iface

# Workaround to let code-completion think, this is subclass of Iface
Iface = object


class BaseApi(Iface):

    def __init__(self, core, user):
        # Only for auto completion, this class can not be instantiated
        from pyload import Core
        from pyload.datatype import User
        assert isinstance(core, Core)
        assert issubclass(BaseApi, Iface)
        self.pyload = core
        assert isinstance(user, User)
        self.user = user
        self.primary_uid = 0
        # No instantiating!
        raise Exception
