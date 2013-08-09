#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from pyload.utils import json
except ImportError:
    import json


import apitypes
from apitypes import BaseObject
from apitypes import ExceptionObject

# compact json separator
separators = (',', ':')

# json encoder that accepts api objects

class BaseEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, BaseObject) or isinstance(o, ExceptionObject):
            ret = {"@class" : o.__class__.__name__}
            for att in o.__slots__:
                ret[att] = getattr(o, att)
            return ret

        return json.JSONEncoder.default(self, o)

# more compact representation, only clients with information of the classes can handle it

class BaseEncoderCompact(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, BaseObject) or isinstance(o, ExceptionObject):
            ret = {"@compact" : [o.__class__.__name__]}
            ret["@compact"].extend(getattr(o, attr) for attr in o.__slots__)
            return ret

        return json.JSONEncoder.default(self, o)

def convert_obj(dct):
    if '@class' in dct:
        cls = getattr(apitypes, dct['@class'])
        del dct['@class']
        return cls(**dct)
    elif '@compact' in dct:
        cls = getattr(apitypes, dct['@compact'][0])
        return cls(*dct['@compact'][1:])

    return dct

def dumps(*args, **kwargs):
    if 'compact' in kwargs and kwargs['compact']:
        kwargs['cls'] = BaseEncoderCompact
        del kwargs['compact']
    else:
        kwargs['cls'] = BaseEncoder

    kwargs['separators'] = separators
    return json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs['object_hook'] = convert_obj
    return json.loads(*args, **kwargs)