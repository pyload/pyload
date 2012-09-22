#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.common.json_layer import json
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

class BaseDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, *args, **kwargs)
        self.object_hook = self.convertObject

    def convertObject(self, dct):
        if '@class' in dct:
            # TODO: convert
            pass

        return dct

def dumps(*args, **kwargs):
    kwargs['cls'] = BaseEncoder
    return json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs['cls'] = BaseDecoder
    return json.loads(*args, **kwargs)