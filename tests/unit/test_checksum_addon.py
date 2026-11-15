"""
Unit tests for the Checksum addon's file hashing.
"""
import os
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pyload.plugins.addons.Checksum import compute_checksum


class TestComputeChecksum(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as fp:
            fp.write(b"pyload" * 5000)

    def tearDown(self):
        os.remove(self.path)

    def test_crc32(self):
        expected = "{:08x}".format(zlib.crc32(b"pyload" * 5000))
        self.assertEqual(compute_checksum(self.path, "crc32").zfill(8), expected)


if __name__ == "__main__":
    unittest.main()
