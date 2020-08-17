# -*- coding: utf-8 -*-

import bitmath

from .check import is_mapping, is_iterable


def convert(obj, rule, func, args=(), kwargs=None, fallback=None):
    if kwargs is None:
        kwargs = {}
    res = None
    cvargs = (rule, func, args, kwargs, fallback)
    try:
        if rule(obj):
            res = func(obj, *args, **kwargs)
        elif is_mapping(obj):
            res = dict(
                (convert(k, *cvargs), convert(v, *cvargs)) for k, v in obj.items()
            )
        elif is_iterable(obj):
            res = type(obj)(convert(i, *cvargs) for i in obj)
        else:
            res = obj
    except Exception as exc:
        if callable(fallback):
            fbargs = cvargs[:-1] + (exc,)
            return fallback(obj, *fbargs)
        raise
    return res


BYTE_PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")


def size(value, in_unit, out_unit):
    """Convert file size."""
    in_unit = in_unit.strip()[0].upper()
    out_unit = out_unit.strip()[0].upper()

    if in_unit == out_unit:
        return value

    in_unit += "yte" if in_unit == "B" else "iB"
    out_unit += "yte" if out_unit == "B" else "iB"

    try:
        # Create a bitmath instance representing the input value with its
        # corresponding unit
        in_size = getattr(bitmath, in_unit)(value)
        # Call the instance method to convert it to the output unit
        out_size = getattr(in_size, "to_" + out_unit)()
        return out_size.value

    except AttributeError:
        sizemap = {u[0]: i * 10 for i, u in enumerate(BYTE_PREFIXES)}

        in_magnitude = sizemap[in_unit]
        out_magnitude = sizemap[out_unit]

        magnitude = in_magnitude - out_magnitude
        i, d = divmod(value, 1)

        decimal = int(d * (1024 ** (abs(magnitude) // 10)))
        if magnitude >= 0:
            integer = int(i) << magnitude
        else:
            integer = int(i) >> magnitude * -1
            decimal = -decimal

        return integer + decimal


def to_bytes(obj, encoding="utf-8", errors="strict"):
    try:
        return obj.encode(encoding, errors)
    except AttributeError:
        return bytes(obj, encoding)


def to_str(obj, encoding="utf-8", errors="strict"):
    try:
        return obj.decode(encoding, errors)
    except AttributeError:
        return str(obj)


# def to_dict(obj):
# """Convert object to dictionary."""
# return dict((attr, getattr(obj, attr)) for attr in obj.__slots__)


def to_list(obj):
    """Convert value to a list with value inside."""
    if isinstance(obj, list):
        pass
    elif is_mapping(obj):
        return list(obj.items())
    elif is_iterable(obj, strict=False):
        return list(obj)
    elif obj is not None:
        return [obj]
    else:
        return list(obj)
