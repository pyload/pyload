# -*- coding: utf-8 -*-

from nose.tools import nottest

from module.network.HTTPDownload import HTTPDownload

import hashlib

def checksum_md5(filename):
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

@nottest
def test_accents_download():
    url = "http://speedtest.netcologne.de/test_1mb.bin"

    #Quick and dirty logger
    import logging
    import logging.handlers
    import sys
    from os.path import join
    log = logging.getLogger("log")
    console = logging.StreamHandler(sys.stdout)
    frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
    console.setFormatter(frm)
    log.addHandler(console) #if console logging
    file_handler = logging.FileHandler('log.txt', encoding="utf8")
    file_handler.setFormatter(frm)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)

    #Create some dummies to avoid errors
    import __builtin__
    __builtin__._ = lambda x: x

    from module.network.Bucket import Bucket

    bucket = Bucket()
    bucket.setRate(200 * 1024)
    bucket = None

    print "starting"

    # Download
    filename = u"é.bin"
    dwnld = HTTPDownload(url, filename, bucket=bucket, options={'interface': None, 'proxies': None, 'ipv6': None})  # FIXME !
    dwnld.download(chunks=3, resume=True)

    # Check hash
    hash = checksum_md5(filename)
    assert hash == "d3e59e91bba5779d881dec449be9d6fc"

    # Cleanup
    os.remove(filename)

if __name__ == '__main__':
    test_accents_download()

