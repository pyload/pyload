import unittest

from pyload.core.utils.web.parse import name


class TestParse(unittest.TestCase):
    def test_name_with_hash(self):
        actual = name('Some file #3 of 5.pdf')
        self.assertEqual(actual, 'Some file #3 of 5.pdf')


if __name__ == '__main__':
    unittest.main()
