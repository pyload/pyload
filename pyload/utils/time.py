# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import datetime
import time as _time
from time import *

from future import standard_library
standard_library.install_aliases()


def compare(start, end):
    if start == end:
        return True

    now = list(_time.localtime()[3:5])
    if (start < now < end or
        start < now > end < start or
            start > end and (now > start or now < end)):
        return True

    return False


def to_midnight(utc=None):
    if utc is None:
        now = datetime.datetime.today()
    else:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=utc)
    midnight = now.replace(hour=0, minute=1, second=0,
                           microsecond=0) + datetime.timedelta(days=1)
    return (midnight - now).seconds


def to_nexthour():
    now = datetime.datetime.today()
    nexthour = now.replace(
        minute=1, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return (nexthour - now).seconds

# Cleanup
del _time, datetime
