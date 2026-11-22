import pytest

from pyload.core.utils.purge import (
    _MACBADCHARS,
    _UNIXBADCHARS,
    _WINBADCHARS,
    _WINBADWORDS,
    name,
)


class TestPurgeName:
    """Tests for the purge.name function."""

    @pytest.mark.parametrize(
        "filename",
        [
            "simple.txt",
            "my_file_123.tar.gz",
            "archive-v1.0.0.zip",
            "document (final) [reviewed].pdf",
            "filename with spaces.txt",
            "file#1$2%3&4'5~6.dat",
            "документ_2024.pdf",
            "日本語_ファイル.txt",
            "résumé_français.docx",
            "emoji_🎬_video.mp4",
        ],
    )
    def test_valid_names_remain_unchanged(self, filename):
        """Valid filenames without bad characters should remain unchanged."""
        assert name(filename) == filename

    @pytest.mark.parametrize("char", _WINBADCHARS)
    def test_individual_bad_characters_replaced_with_default_sep(self, char):
        """Every invalid character across Windows/Mac/Unix should be replaced by '_'."""
        input_name = f"prefix{char}suffix"
        assert name(input_name) == "prefix_suffix"

    @pytest.mark.parametrize("char", _UNIXBADCHARS)
    def test_unix_bad_characters(self, char):
        """Unix bad characters (\\0, /, \\) should be replaced."""
        assert name(f"dir{char}file") == "dir_file"

    @pytest.mark.parametrize("char", _MACBADCHARS)
    def test_mac_bad_characters(self, char):
        """Mac bad characters should include colon ':' and be replaced."""
        assert name(f"file{char}stream") == "file_stream"

    def test_multiple_and_consecutive_bad_characters(self):
        """Multiple and consecutive bad characters are replaced."""
        assert name('a<b|c>d"e*f?g:h/i\\j\0k') == "a_b_c_d_e_f_g_h_i_j_k"
        assert name("file///name") == "file___name"
        assert name("file:<?*>.txt") == "file_____.txt"

    @pytest.mark.parametrize(
        "sep, expected",
        [
            ("-", "file-name-test.txt"),
            ("", "filenametest.txt"),
            ("__", "file__name__test.txt"),
            (".", "file.name.test.txt"),
            ("~", "file~name~test.txt"),
        ],
    )
    def test_custom_separator(self, sep, expected):
        """Invalid characters should be replaced with the specified separator."""
        assert name("file/name:test.txt", sep=sep) == expected

    def test_whitespace_allowed_by_default(self):
        """By default, allow_whitespaces is True and internal spaces are preserved."""
        assert name("a file with spaces.txt") == "a file with spaces.txt"
        assert name("  leading and trailing.txt  ") == "leading and trailing.txt"
        assert name("multi   spaced   name.txt") == "multi   spaced   name.txt"

    def test_whitespace_disallowed(self):
        """When allow_whitespaces is False, spaces are replaced with the separator."""
        assert name("a file with spaces.txt", allow_whitespaces=False) == "a_file_with_spaces.txt"
        assert name("hello world.txt", sep="-", allow_whitespaces=False) == "hello-world.txt"
        assert name("hello world.txt", sep="", allow_whitespaces=False) == "helloworld.txt"
        assert name("hello   world.txt", allow_whitespaces=False) == "hello___world.txt"
        # Leading and trailing spaces are replaced by sep
        assert name("  hello world  ", allow_whitespaces=False) == "__hello_world__"

    def test_whitespace_stripping(self):
        """Leading and trailing whitespace characters (spaces, tabs, newlines) are stripped."""
        assert name("   filename.txt   ") == "filename.txt"
        assert name("\tfilename.txt\n") == "filename.txt"
        assert name("\r\n  filename.txt  \r\n") == "filename.txt"

    @pytest.mark.parametrize("badword", _WINBADWORDS)
    def test_windows_bad_words_prefixed(self, badword):
        """Windows reserved device names should be prefixed with the separator."""
        assert name(badword) == f"_{badword}"

    @pytest.mark.parametrize(
        "badword_case",
        [
            "CON",
            "Con",
            "AUX",
            "Aux",
            "PRN",
            "Prn",
            "NUL",
            "Nul",
            "COM1",
            "Com5",
            "LPT1",
            "Lpt9",
        ],
    )
    def test_windows_bad_words_case_insensitive(self, badword_case):
        """Windows reserved names should be detected case-insensitively and preserve original case."""
        assert name(badword_case) == f"_{badword_case}"

    def test_windows_bad_words_with_custom_sep(self):
        """Reserved device names use custom sep or fall back to '_' when sep is empty."""
        assert name("con", sep="-") == "-con"
        assert name("aux", sep="~") == "~aux"
        assert name("nul", sep="") == "_nul"

    def test_windows_bad_words_with_surrounding_whitespace(self):
        """Reserved device names surrounded by whitespace should still be detected after stripping."""
        assert name("  con  ") == "_con"
        assert name("  AUX  ", sep="-") == "-AUX"

    @pytest.mark.parametrize(
        "name_variant",
        [
            "con.txt",
            "contact.doc",
            "auxiliary.py",
            "prnt.log",
            "nulled.dat",
            "com10",
            "lpt0",
            "lpt10",
        ],
    )
    def test_names_containing_bad_words_not_prefixed(self, name_variant):
        """Filenames that merely contain or start with a bad word should not be prefixed."""
        assert name(name_variant) == name_variant

    def test_windows_bad_word_with_bad_chars(self):
        """Names where bad characters are replaced resulting in non-reserved words."""
        assert name("c/o/n") == "c_o_n"
        assert name("con/1") == "con_1"

    def test_empty_and_whitespace_only_strings(self):
        """Empty string or string with only whitespace should return empty string."""
        assert name("") == ""
        assert name("   ") == ""
        assert name("\t\n\r") == ""

    def test_bad_characters_only(self):
        """String containing only bad characters produces only separators or empty string."""
        assert name("///") == "___"
        assert name("///", sep="") == ""
        assert name("<<<>>>", sep="-") == "------"
