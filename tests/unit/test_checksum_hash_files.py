"""
Unit tests for parsing the hash files read by the Checksum addon.
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pyload.plugins.addons.Checksum import Checksum


class TestMd5File(unittest.TestCase):
    def test_md5sum_line(self):
        for line in (
            "3abd21e40e63e2b0ab4e1b00b40ebc23  movie.part1.rar",
            "3abd21e40e63e2b0ab4e1b00b40ebc23 *movie.part1.rar",
        ):
            m = re.match(Checksum._regexmap["md5"], line)
            self.assertEqual(m.group("HASH"), "3abd21e40e63e2b0ab4e1b00b40ebc23")
            self.assertEqual(m.group("NAME"), "movie.part1.rar")


if __name__ == "__main__":
    unittest.main()
