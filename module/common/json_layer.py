#!/usr/bin/env python
# -*- coding: utf-8 -*-


# abstraction layer for json operations

try: # since python 2.7
    from json import loads as json_loads
    from json import dumps as json_dumps
except ImportError:
    from module.lib.simplejson import loads as json_loads
    from module.lib.simplejson import dumps as json_dumps