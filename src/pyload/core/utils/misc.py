# -*- coding: utf-8 -*-

import random
import string
import sys

if sys.version_info < (3, 12):
    def monkey_patch():
        """Patching js2py for CVE-2024-28397"""
        from js2py.constructors.jsobject import Object
        fn = Object.own["getOwnPropertyNames"]["value"].code

        def wraps(*args, **kwargs):
            result = fn(*args, **kwargs)
            return list(result)
        Object.own["getOwnPropertyNames"]["value"].code = wraps

    import js2py
    monkey_patch()
    js2py.disable_pyimport()

else:
    import dukpy


def random_string(length, valid_chars=string.ascii_letters + string.digits + string.punctuation):
    return "".join(random.choice(valid_chars) for _ in range(length))


def is_plural(value):
    try:
        n = abs(float(value))
        return n == 0 or n > 1
    except ValueError:
        return value.endswith("s")  # TODO: detect uncommon plurals


def eval_js(script, es6=False):
    if sys.version_info < (3, 12):
        return (js2py.eval_js6 if es6 else js2py.eval_js)(script)
    else:
        return dukpy.evaljs(script)


def accumulate(iterable, to_map=None):
    """
    Accumulate (key, value) data to {value : [key]} dictionary.
    """
    if to_map is None:
        to_map = {}
    for key, value in iterable:
        to_map.setdefault(value, []).append(key)
    return to_map


def reversemap(obj):
    """
    Invert mapping object preserving type and ordering.
    """
    return obj.__class__(reversed(item) for item in obj.items())


# def get_translation(domain, localedir=None, languages=None, class_=None,
# fallback=False, codeset=None):
# try:
# trans = gettext.translation(
# domain, localedir, languages, class_, False, codeset)
# except (IOError, OSError):
# if not fallback:
# raise
# trans = gettext.translation(
# domain, localedir, None, class_, fallback, codeset)
# return trans


# def install_translation(domain, localedir=None, languages=None,
# class_=None, fallback=False, codeset=None):
# trans = get_translation(
# domain, localedir, languages, class_, fallback, codeset)
# try:
# trans.install(str=True)
# except TypeError:
# trans.install()
