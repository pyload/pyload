# -*- coding: utf-8 -*-

from nose.tools import nottest
import hashlib

import common_init
from module.network.HTTPDownload import HTTPDownload

def checksum_md5(filename):
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

@nottest
def test_accents_download():
    url = "http://speedtest.netcologne.de/test_1mb.bin"

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

