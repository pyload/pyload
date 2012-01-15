
from unittest import TestCase

from pyLoadCore import Core
from module.common.APIExerciser import APIExerciser

class TestApi(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        cls.core.start(False, False, True)

    def test_random(self):
        api = APIExerciser(self.core)

        for i in range(2000):
            api.testAPI()