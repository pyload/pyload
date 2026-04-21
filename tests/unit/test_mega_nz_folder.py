import re

from pyload.plugins.decrypters.MegaCoNzFolder import MegaCoNzFolder


class TestMegaNzFolder:
    def test_folder_pattern(self):
        url = 'https://mega.nz/folder/abc123#789def_abcdef123'
        actual = re.match(MegaCoNzFolder.__pattern__, url).groupdict()
        assert actual == {'ID': 'abc123', 'KEY': '789def_abcdef123', 'SUBDIR': None}

    def test_subfolder_pattern(self):
        url = 'https://mega.nz/folder/abc123#789def_abcdef123/folder/111222333'
        actual = re.match(MegaCoNzFolder.__pattern__, url).groupdict()
        assert actual == {'ID': 'abc123', 'KEY': '789def_abcdef123', 'SUBDIR': '111222333'}
