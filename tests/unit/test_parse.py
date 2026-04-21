from pyload.core.utils.web.parse import name


class TestParse:
    def test_name_with_hash(self):
        actual = name('Some file #3 of 5.pdf')
        assert actual == 'Some file #3 of 5.pdf'

    def test_name_with_semicolon(self):
        actual = name('Some file;x.pdf')
        assert actual == 'Some file;x.pdf'

