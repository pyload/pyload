import pytest

from pyload.core.utils.purge import name


class TestName:
    @pytest.mark.parametrize("reserved", ["con", "prn", "aux", "nul", "com1", "lpt9"])
    def test_windows_reserved_names_are_prefixed(self, reserved):
        assert name(reserved) == f"_{reserved}"

    @pytest.mark.parametrize("reserved", ["AUX", "Nul"])
    def test_windows_reserved_names_are_case_insensitive(self, reserved):
        assert name(reserved) == f"_{reserved}"

    def test_regular_name_is_unchanged(self):
        assert name("auxiliary.txt") == "auxiliary.txt"
