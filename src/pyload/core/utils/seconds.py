# -*- coding: utf-8 -*-

import datetime
import time


def compare(start, end):
    start = tuple(int(n) for n in start)
    end = tuple(int(n) for n in end)

    if start == end:
        return True

    now = time.localtime()[3:5]
    if start < now < end or start < now > end < start:
        return True

    elif start > end and (now > start or now < end):
        return True

    return False


def to_midnight(utc=None, strict=False):
    if utc is None:
        now = datetime.datetime.today()
    else:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=utc)

    midnight = now.replace(
        hour=0, minute=0 if strict else 1, second=0, microsecond=0
    ) + datetime.timedelta(days=1)

    return (midnight - now).total_seconds()


def to_nexthour(strict=False):
    now = datetime.datetime.today()
    nexthour = now.replace(
        minute=0 if strict else 1, second=0, microsecond=0
    ) + datetime.timedelta(hours=1)
    return (nexthour - now).seconds
