# -*- coding: utf-8 -*-

# TODO: Move to utils directory in 0.6.x

import hashlib
import itertools
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import traceback
import zlib
from base64 import b85decode, b85encode
from collections.abc import Sequence
from datetime import timedelta


class Config:
    def __init__(self, plugin):
        self.plugin = plugin

    def set(self, option, value, plugin=None):
        """
        Set config value for current plugin.

        :param option:
        :param value:
        :return:
        """
        self.plugin.pyload.api.set_config_value(
            plugin or self.plugin.classname, option, value, section="plugin"
        )

    def get(self, option, default=None, plugin=None):
        """
        Returns config value for current plugin.

        :param option:
        :return:
        """
        try:
            return self.plugin.pyload.config.get_plugin(
                plugin or self.plugin.classname, option
            )

        except KeyError:
            self.plugin.log_debug(
                "Config option `{}` not found, use default `{}`".format(option, default)
            )  # TODO: Restore to `log_warning` in 0.6.x
            return default


class DB:
    def __init__(self, plugin):
        self.plugin = plugin

    def store(self, key, value):
        """
        Saves a value persistently to the database.
        """
        # NOTE: value must not be <bytes> otherwise BOOM! and moreover our sqlite db always return strings as <str>
        entry = b85encode(json.dumps(value, ensure_ascii=False).encode()).decode()
        self.plugin.pyload.db.set_storage(self.plugin.classname, key, entry)

    def retrieve(self, key=None, default=None):
        """
        Retrieves saved value or dict of all saved entries if key is None.
        """
        entry = self.plugin.pyload.db.get_storage(self.plugin.classname, key)

        if key:
            if entry is None:
                value = default
            else:
                value = json.loads(b85decode(entry).decode())
        else:
            if not entry:
                value = default
            else:
                value = {k: json.loads(b85decode(v).decode()) for k, v in value.items()}

        return value

    def delete(self, key):
        """
        Delete entry in db.
        """
        self.plugin.pyload.db.del_storage(self.plugin.classname, key)


class Periodical:
    def __init__(self, plugin, task=lambda x: x, interval=None):
        self.plugin = plugin
        self.task = task
        self.cb = None
        self._ = self.plugin.pyload
        self.interval = interval

    def set_interval(self, value):
        newinterval = max(0, value)

        if newinterval != value:
            return False

        if newinterval != self.interval:
            self.interval = newinterval

        return True

    def start(self, interval=None, threaded=False, delay=0):
        if interval is not None and self.set_interval(interval) is False:
            return False
        else:
            self.cb = self.plugin.pyload.scheduler.add_job(
                max(1, delay), self._task, [threaded], threaded=threaded
            )
            return True

    def restart(self, *args, **kwargs):
        self.stop()
        return self.start(*args, **kwargs)

    def stop(self):
        try:
            return self.plugin.pyload.scheduler.remove_job(self.cb)

        except Exception:
            return False

        finally:
            self.cb = None

    stopped = property(lambda self: self.cb is None)

    def _task(self, threaded):
        try:
            self.task()

        except Exception as exc:
            self.plugin.log_error(self._("Error performing periodical task"), exc)

        if not self.stopped:
            self.restart(threaded=threaded, delay=self.interval)


class SimpleQueue:
    def __init__(self, plugin, storage="queue"):
        self.plugin = plugin
        self.storage = storage

    def get(self):
        return self.plugin.db.retrieve(self.storage, default=[])

    def set(self, value):
        return self.plugin.db.store(self.storage, value)

    def delete(self):
        return self.plugin.db.delete(self.storage)

    def add(self, item):
        queue = self.get()
        if item not in queue:
            return self.set(queue + [item])
        else:
            return True

    def remove(self, item):
        queue = self.get()
        try:
            queue.remove(item)

        except ValueError:
            pass

        if isinstance(queue, list):
            return self.delete()

        return self.set(queue)


def sign_string(message, pem_private, pem_passphrase="", sign_algo="SHA384"):
    """
    Generate a signature for string using the `sign_algo` and `RSA` algorithms.
    """
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Signature import PKCS1_v1_5
    from binascii import b2a_hex

    if sign_algo not in ("MD5", "SHA1", "SHA256", "SHA384", "SHA512"):
        raise ValueError("Unsupported Signing algorithm")

    priv_key = RSA.import_key(pem_private, passphrase=pem_passphrase)
    signer = PKCS1_v1_5.new(priv_key)
    digest = getattr(
        __import__("Cryptodome.Hash", fromlist=[sign_algo]), sign_algo
    ).new()
    digest.update(message)
    return b2a_hex(signer.sign(digest))


def fsbsize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    path = os.fsdecode(path)

    if os.name == "nt":
        import ctypes

        drive = "{}\\".format(os.path.splitdrive(path)[0])
        cluster_sectors, sector_size = ctypes.c_longlong(0)

        ctypes.windll.kernel32.GetDiskFreeSpaceW(
            ctypes.c_wchar_p(drive),
            ctypes.pointer(cluster_sectors),
            ctypes.pointer(sector_size),
            None,
            None,
        )
        return cluster_sectors * sector_size

    else:
        return os.statvfs(path).f_frsize


def has_method(obj, name):
    """
    Check if function 'name' was defined in obj.
    """
    return callable(getattr(obj, name, None))


def isiterable(obj):
    """
    Check if object is iterable (string excluded)
    """
    return hasattr(obj, "__iter__")


def is_sequence(obj):
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))


def get_console_encoding(enc):
    if os.name == "nt":
        if enc == "cp65001":  #: aka UTF-8
            enc = "cp850"
            # print("WARNING: Windows codepage 65001 (UTF-8) is not supported, used `{}` instead".format(enc))
    else:
        enc = "utf-8"

    return enc


def exists(path):
    path = os.fsdecode(path)

    if os.path.exists(path):
        if os.name == "nt":
            dir, name = os.path.split(path.rstrip(os.sep))
            name_lw = name.lower()
            return any(True for entry in os.listdir(dir) if entry.lower() == name_lw)
        else:
            return True
    else:
        return False


def str2int(value):
    try:
        return int(value)
    except Exception:
        pass

    ones = (
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    )
    tens = (
        "",
        "",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
    )

    o_tuple = [(w, i) for i, w in enumerate(ones)]
    t_tuple = [(w, i * 10) for i, w in enumerate(tens)]

    numwords = dict(o_tuple + t_tuple)
    tokens = re.split(r"[\s\-]+", value.lower())

    try:
        return sum(numwords[word] for word in tokens)
    except Exception:
        return 0


def timestamp():
    return int(time.time() * 1000)


def check_module(module):
    try:
        __import__(module)

    except Exception:
        return False

    else:
        return True


def check_prog(command):
    pipe = subprocess.PIPE
    try:
        subprocess.call(command, stdout=pipe, stderr=pipe)

    except Exception:
        return False

    else:
        return True


def is_executable(filename):
    file = os.fsdecode(filename)
    return os.path.isfile(file) and os.access(file, os.X_OK)


def which(filename):
    """
    Works exactly like the unix command which Courtesy of
    http://stackoverflow.com/a/377028/675646.
    """
    dirname, basename = os.path.split(filename)

    if dirname:
        return filename if is_executable(filename) else None

    else:
        for path in os.environ["PATH"].split(os.pathsep):
            filename = os.path.join(path.strip('"'), filename)
            if is_executable(filename):
                return filename


def format_exc(frame=None):
    """
    Format call-stack and display exception information (if availible)
    """
    exc_info = sys.exc_info()
    exc_desc = ""

    callstack = traceback.extract_stack(frame)
    callstack = callstack[:-1]

    if exc_info[0] is not None:
        exception_callstack = traceback.extract_tb(exc_info[2])

        # NOTE: Does this exception belongs to us?
        if callstack[-1][0] == exception_callstack[0][0]:
            callstack = callstack[:-1]
            callstack.extend(exception_callstack)
            exc_desc = "".join(
                traceback.format_exception_only(exc_info[0], exc_info[1])
            )

    msg = "Traceback (most recent call last):\n"
    msg += "".join(traceback.format_list(callstack))
    msg += exc_desc

    return msg


def replace_patterns(value, rules):
    for r in rules:
        try:
            pattern, repl, flags = r

        except ValueError:
            pattern, repl = r
            flags = 0

        value = re.sub(pattern, repl, value, flags)

    return value


# TODO: Remove in 0.6.x and fix exp in CookieJar.set_cookie
def set_cookie(
    cj, domain, name, value, path="/", exp=time.time() + timedelta(hours=744).seconds
):  #: 31 days retention
    args = [domain, name, value, path, int(exp)]
    return cj.set_cookie(*args)


def set_cookies(cj, cookies):
    for cookie in cookies:
        if not isinstance(cookie, tuple):
            continue

        if len(cookie) != 3:
            continue

        set_cookie(cj, *cookie)


def parse_html_header(header):
    header = str(header)

    hdict = {}
    _re = r"[ ]*(?P<key>.+?)[ ]*:[ ]*(?P<value>.+?)[ ]*\r?\n"

    for key, value in re.findall(_re, header):
        key = key.lower()
        if key in hdict:
            header_key = hdict.get(key)
            if isinstance(header_key, list):
                header_key.append(value)
            else:
                hdict[key] = [header_key, value]
        else:
            hdict[key] = value

    return hdict


def parse_html_tag_attr_value(attr_name, tag):
    m = re.search(
        r'{}\s*=\s*(["\']?)((?<=")[^"]+|(?<=\')[^\']+|[^>\s"\'][^>\s]*)\1'.format(
            attr_name
        ),
        tag,
        re.I,
    )
    return m.group(2) if m else None


def parse_html_form(attr_str, html, input_names={}):
    for form in re.finditer(
        r"(?P<TAG><form[^>]*{}.*?>)(?P<CONTENT>.*?)</?(form|body|html).*?>".format(
            attr_str
        ),
        html,
        re.I | re.S,
    ):
        inputs = {}
        action = parse_html_tag_attr_value("action", form.group("TAG"))

        for inputtag in re.finditer(
            r"(<(input|textarea).*?>)([^<]*(?=</\2)|)",
            re.sub(re.compile(r"<!--.+?-->", re.I | re.S), "", form.group("CONTENT")),
            re.I | re.S,
        ):

            name = parse_html_tag_attr_value("name", inputtag.group(1))
            if name:
                value = parse_html_tag_attr_value("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ""
                else:
                    inputs[name] = value

        if not input_names:
            #: No attribute check
            return action, inputs
        else:
            #: Check input attributes
            for key, value in input_names.items():
                if key in inputs:
                    if isinstance(value, str) and inputs[key] == value:
                        continue
                    elif isinstance(value, tuple) and inputs[key] in value:
                        continue
                    elif hasattr(value, "search") and re.match(value, inputs[key]):
                        continue
                    else:
                        break  #: Attibute value does not match
                else:
                    break  #: Attibute name does not match
            else:
                return action, inputs  #: Passed attribute check

    return None, None  #: No matching form found


def chunks(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


def renice(pid, value):
    if not value or os.name == "nt":
        return

    try:
        subprocess.Popen(
            ["renice", str(value), str(pid)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=-1,
        )
    except Exception:
        pass


def forward(source, destination):
    try:
        bufsize = 1 << 10
        bufdata = source.recv(bufsize)
        while bufdata:
            destination.sendall(bufdata)
            bufdata = source.recv(bufsize)
    finally:
        destination.shutdown(socket.SHUT_WR)


def compute_checksum(filename, hashtype):
    file = os.fsdecode(filename)

    if not exists(file):
        return None

    buf = fsbsize(filename)

    if hashtype in ("adler32", "crc32"):
        hf = getattr(zlib, hashtype)
        last = 0

        with open(file, mode="rb") as fp:
            for chunk in iter(lambda: fp.read(buf), ""):
                last = hf(chunk, last)

        return "{:x}".format(last)

    elif hashtype in hashlib.algorithms_available:
        h = hashlib.new(hashtype)

        with open(file, mode="rb") as fp:
            for chunk in iter(lambda: fp.read(buf * h.block_size), ""):
                h.update(chunk)

        return h.hexdigest()

    else:
        return None


def copy_tree(src, dst, overwrite=False, preserve_metadata=False):
    pmode = preserve_metadata or overwrite is None
    mtime = os.path.getmtime
    copy = shutil.copy2 if pmode else shutil.copy

    if preserve_metadata and not exists(dst):
        return shutil.copytree(src, dst)

    for src_dir, dirs, files in os.walk(src, topdown=False):
        dst_dir = src_dir.replace(src, dst, 1)

        if not exists(dst_dir):
            os.makedirs(dst_dir)
            if pmode:
                shutil.copystat(src_dir, dst_dir)

        elif pmode:
            if overwrite or overwrite is None and mtime(src_dir) > mtime(dst_dir):
                shutil.copystat(src_dir, dst_dir)

        for filename in files:
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)

            if exists(dst_file):
                if overwrite or overwrite is None and mtime(src_file) > mtime(dst_file):
                    os.remove(dst_file)
                else:
                    continue

            copy(src_file, dst_dir)


def move_tree(src, dst, overwrite=False):
    mtime = os.path.getmtime

    for src_dir, dirs, files in os.walk(src, topdown=False):
        dst_dir = src_dir.replace(src, dst, 1)
        del_dir = True

        if not exists(dst_dir):
            os.makedirs(dst_dir)
            shutil.copystat(src_dir, dst_dir)

        elif overwrite or overwrite is None and mtime(src_dir) > mtime(dst_dir):
            shutil.copystat(src_dir, dst_dir)

        else:
            del_dir = False

        for filename in files:
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)

            if exists(dst_file):
                if overwrite or overwrite is None and mtime(src_file) > mtime(dst_file):
                    os.remove(dst_file)
                else:
                    continue

            shutil.move(src_file, dst_dir)

        if not del_dir:
            continue

        try:
            os.rmdir(src_dir)
        except OSError:
            pass
