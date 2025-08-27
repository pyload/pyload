# -*- coding: utf-8 -*-

import multiprocessing
import random
import string

from py_mini_racer import MiniRacer


def random_string(length, valid_chars=string.ascii_letters + string.digits + string.punctuation):
    return "".join(random.choice(valid_chars) for _ in range(length))


def is_plural(value):
    try:
        n = abs(float(value))
        return n == 0 or n > 1
    except ValueError:
        return value.endswith("s")  # TODO: detect uncommon plurals


def _run_js(script, queue, timeout_seconds, max_memory):
    try:
        ctx = MiniRacer()
        ctx.set_soft_memory_limit(max(1_048_576, max_memory - 1_048_576))
        result = ctx.eval(script, timeout=timeout_seconds*1000, max_memory=max_memory)

        queue.put(("success", result))

    except Exception as exc:
        queue.put(("error", exc))


def eval_js(script, timeout_seconds=5.0, max_memory=10_485_760):  # 10MiB limit
    result_queue = multiprocessing.Queue()

    process = multiprocessing.Process(target=_run_js, args=(script, result_queue, timeout_seconds, max_memory,))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(1.0)
        raise TimeoutError(f"JavaScript execution timed out after {timeout_seconds} seconds")

    status, value = result_queue.get()
    if status == "error":
        raise value

    return value


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
