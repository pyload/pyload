# -*- coding: utf-8 -*-

from __future__ import with_statement

import hashlib
import re
import zlib

from os import remove
from os.path import getsize, isfile, splitext

from module.plugins.Hook import Hook
from module.utils import save_join, fs_encode


def computeChecksum(local_file, algorithm):
    if algorithm in getattr(hashlib, "algorithms", ("md5", "sha1", "sha224", "sha256", "sha384", "sha512")):
        h = getattr(hashlib, algorithm)()

        with open(local_file, 'rb') as f:
            for chunk in iter(lambda: f.read(128 * h.block_size), b''):
                h.update(chunk)

        return h.hexdigest()

    elif algorithm in ("adler32", "crc32"):
        hf = getattr(zlib, algorithm)
        last = 0

        with open(local_file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                last = hf(chunk, last)

        return "%x" % last

    else:
        return None


class Checksum(Hook):
    __name__ = "Checksum"
    __type__ = "hook"
    __version__ = "0.12"

    __config__ = [("activated", "bool", "Activated", False),
                  ("check_action", "fail;retry;nothing", "What to do if check fails?", "retry"),
                  ("max_tries", "int", "Number of retries", 2),
                  ("retry_action", "fail;nothing", "What to do if all retries fail?", "fail"),
                  ("wait_time", "int", "Time to wait before each retry (seconds)", 1)]

    __description__ = """Verify downloaded file size and checksum"""
    __author_name__ = ("zoidberg", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "vuolter@gmail.com")

    methods = {'sfv': 'crc32', 'crc': 'crc32', 'hash': 'md5'}
    regexps = {'sfv': r'^(?P<name>[^;].+)\s+(?P<hash>[0-9A-Fa-f]{8})$',
               'md5': r'^(?P<name>[0-9A-Fa-f]{32})  (?P<file>.+)$',
               'crc': r'filename=(?P<name>.+)\nsize=(?P<size>\d+)\ncrc32=(?P<hash>[0-9A-Fa-f]{8})$',
               'default': r'^(?P<hash>[0-9A-Fa-f]+)\s+\*?(?P<name>.+)$'}


    def coreReady(self):
        if not self.config['general']['checksum']:
            self.logInfo("Checksum validation is disabled in general configuration")

    def setup(self):
        self.algorithms = sorted(
            getattr(hashlib, "algorithms", ("md5", "sha1", "sha224", "sha256", "sha384", "sha512")), reverse=True)
        self.algorithms.extend(["crc32", "adler32"])
        self.formats = self.algorithms + ["sfv", "crc", "hash"]

    def downloadFinished(self, pyfile):
        """
        Compute checksum for the downloaded file and compare it with the hash provided by the hoster.
        pyfile.plugin.check_data should be a dictionary which can contain:
        a) if known, the exact filesize in bytes (e.g. "size": 123456789)
        b) hexadecimal hash string with algorithm name as key (e.g. "md5": "d76505d0869f9f928a17d42d66326307")
        """
        if hasattr(pyfile.plugin, "check_data") and (isinstance(pyfile.plugin.check_data, dict)):
            data = pyfile.plugin.check_data.copy()
        elif hasattr(pyfile.plugin, "api_data") and (isinstance(pyfile.plugin.api_data, dict)):
            data = pyfile.plugin.api_data.copy()
        else:
            return

        self.logDebug(data)

        if not pyfile.plugin.lastDownload:
            self.checkFailed(pyfile, None, "No file downloaded")

        local_file = fs_encode(pyfile.plugin.lastDownload)
        #download_folder = self.config['general']['download_folder']
        #local_file = fs_encode(save_join(download_folder, pyfile.package().folder, pyfile.name))

        if not isfile(local_file):
            self.checkFailed(pyfile, None, "File does not exist")

            # validate file size
        if "size" in data:
            api_size = int(data['size'])
            file_size = getsize(local_file)
            if api_size != file_size:
                self.logWarning("File %s has incorrect size: %d B (%d expected)" % (pyfile.name, file_size, api_size))
                self.checkFailed(pyfile, local_file, "Incorrect file size")
            del data['size']

        # validate checksum
        if data and self.config['general']['checksum']:
            if "checksum" in data:
                data['md5'] = data['checksum']

            for key in self.algorithms:
                if key in data:
                    checksum = computeChecksum(local_file, key.replace("-", "").lower())
                    if checksum:
                        if checksum == data[key].lower():
                            self.logInfo('File integrity of "%s" verified by %s checksum (%s).' %
                                        (pyfile.name, key.upper(), checksum))
                            break
                        else:
                            self.logWarning("%s checksum for file %s does not match (%s != %s)" %
                                           (key.upper(), pyfile.name, checksum, data[key]))
                            self.checkFailed(pyfile, local_file, "Checksums do not match")
                    else:
                        self.logWarning("Unsupported hashing algorithm: %s" % key.upper())
            else:
                self.logWarning("Unable to validate checksum for file %s" % pyfile.name)

    def checkFailed(self, pyfile, local_file, msg):
        check_action = self.getConfig("check_action")
        if check_action == "retry":
            max_tries = self.getConfig("max_tries")
            retry_action = self.getConfig("retry_action")
            if pyfile.plugin.retries < max_tries:
                if local_file:
                    remove(local_file)
                pyfile.plugin.retry(max_tries=max_tries, wait_time=self.getConfig("wait_time"), reason=msg)
            elif retry_action == "nothing":
                return
        elif check_action == "nothing":
            return
        pyfile.plugin.fail(reason=msg)

    def packageFinished(self, pypack):
        download_folder = save_join(self.config['general']['download_folder'], pypack.folder, "")

        for link in pypack.getChildren().itervalues():
            file_type = splitext(link['name'])[1][1:].lower()
            #self.logDebug(link, file_type)

            if file_type not in self.formats:
                continue

            hash_file = fs_encode(save_join(download_folder, link['name']))
            if not isfile(hash_file):
                self.logWarning("File not found: %s" % link['name'])
                continue

            with open(hash_file) as f:
                text = f.read()

            for m in re.finditer(self.regexps.get(file_type, self.regexps['default']), text):
                data = m.groupdict()
                self.logDebug(link['name'], data)

                local_file = fs_encode(save_join(download_folder, data['name']))
                algorithm = self.methods.get(file_type, file_type)
                checksum = computeChecksum(local_file, algorithm)
                if checksum == data['hash']:
                    self.logInfo('File integrity of "%s" verified by %s checksum (%s).' %
                                (data['name'], algorithm, checksum))
                else:
                    self.logWarning("%s checksum for file %s does not match (%s != %s)" %
                                   (algorithm, data['name'], checksum, data['hash']))
