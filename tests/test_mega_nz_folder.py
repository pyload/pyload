import re
import unittest

from pyload.plugins.decrypters.MegaCoNzFolder import MegaCoNzFolder


class TestParse(unittest.TestCase):
    def test_folder_pattern(self):
        url = 'https://mega.nz/folder/abc123#789def_abcdef123'
        actual = re.match(MegaCoNzFolder.__pattern__, url).groupdict()
        self.assertEqual(actual, {'ID': 'abc123', 'KEY': '789def_abcdef123', 'SUBDIR': None})

    def test_subfolder_pattern(self):
        url = 'https://mega.nz/folder/abc123#789def_abcdef123/folder/111222333'
        actual = re.match(MegaCoNzFolder.__pattern__, url).groupdict()
        self.assertEqual(actual, {'ID': 'abc123', 'KEY': '789def_abcdef123', 'SUBDIR': '111222333'})


if __name__ == '__main__':
    unittest.main()
