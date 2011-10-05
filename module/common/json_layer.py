#!/usr/bin/env python
# -*- coding: utf-8 -*-

# abstraction layer for json operations

try: # since python 2.6
    import json
    from json import loads as json_loads
    from json import dumps as json_dumps
except ImportError: #use system simplejson if available
    import simplejson as json
    from simplejson import loads as json_loads
    from simplejson import dumps as json_dumps
