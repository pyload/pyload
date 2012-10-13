#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from module.common.json_layer import json
except ImportError:
    import json


import ttypes
from ttypes import BaseObject

# json encoder that accepts TBase objects
class BaseEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, BaseObject):
            ret = {"@class" : o.__class__.__name__}
            for att in o.__slots__:
                ret[att] = getattr(o, att)
            return ret

        return json.JSONEncoder.default(self, o)


def convert_obj(dct):
    if '@class' in dct:
        cls = getattr(ttypes, dct['@class'])
        del dct['@class']
        return cls(**dct)

def dumps(*args, **kwargs):
    kwargs['cls'] = BaseEncoder
    return json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs['object_hook'] = convert_obj
    return json.loads(*args, **kwargs)