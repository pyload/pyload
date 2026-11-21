import pytest

from pyload.core.utils.web.parse import disposition, name


class TestParse:
    def test_name_with_hash(self):
        actual = name('Some file #3 of 5.pdf')
        assert actual == 'Some file #3 of 5.pdf'

    def test_name_with_semicolon(self):
        actual = name('Some file;x.pdf')
        assert actual == 'Some file;x.pdf'


class TestDisposition:
    def test_basic_filename(self):
        assert disposition("attachment; filename=test.txt") == "test.txt"
        assert disposition('attachment; filename="document.pdf"') == "document.pdf"
        assert disposition('inline; filename="preview.png"') == "preview.png"
        assert disposition('form-data; name="upload"; filename="data.csv"') == "data.csv"
        assert disposition('attachment; size=1024; filename="archive.tar.gz"') == "archive.tar.gz"
        assert disposition('attachment; FILENAME="report.docx"') == "report.docx"
        assert disposition('attachment; filename="  spaced.txt  "') == "spaced.txt"
        assert disposition('attachment; filename="foo;bar.txt"') == "foo;bar.txt"

    def test_quoted_and_escaped_characters(self):
        assert disposition(r'attachment; filename="my \"quote\".txt"') == "my _quote_.txt"
        assert disposition(r'attachment; filename="foo\\bar.txt"') == "bar.txt"

    def test_header_parsing_edge_cases(self):
        # Multiple/consecutive semicolons
        assert disposition('attachment;; filename="double_semi.txt";;') == "double_semi.txt"
        # Tabs and extra spaces around delimiters
        assert disposition('attachment \t;  filename = "spaced_param.txt" ; size = 500') == "spaced_param.txt"
        # Mixed-case parameter names
        assert disposition('attachment; FiLeNaMe="mixed_case.txt"') == "mixed_case.txt"
        assert disposition('attachment; FILENAME*="utf-8\'\'mixed_star.txt"') == "mixed_star.txt"
        # Multiple parameters with filename in middle or end
        assert disposition('attachment; size=123; filename="middle.txt"; extra=val') == "middle.txt"
        assert disposition('attachment; extra=val; filename="last.txt"') == "last.txt"
        # Parameter without value or equals
        assert disposition("attachment; filename") is None
        assert disposition("attachment; filename=") is None
        # Unquoted filename with dots, dashes, underscores
        assert disposition("attachment; filename=archive_v1.0.2-final.tar.gz") == "archive_v1.0.2-final.tar.gz"

    def test_rfc5987_filename_star(self):
        assert disposition("attachment; filename*=UTF-8'en'%c2%a3%20rates.txt") == "£ rates.txt"
        assert disposition("attachment; filename*=UTF-8''foo-%c3%a4.html") == "foo-ä.html"
        assert disposition("attachment; filename*=iso-8859-1''%A3%20rates.txt") == "£ rates.txt"

    def test_rfc5987_extended_edge_cases(self):
        # Single quotes within percent-encoded filename
        assert disposition("attachment; filename*=UTF-8''%27quoted%27.txt") == "'quoted'.txt"
        # Charset other than UTF-8 / ISO-8859-1 (windows-1252 with %80 euro symbol)
        assert disposition("attachment; filename*=windows-1252''%80%20rates.txt") == "€ rates.txt"
        # Language tag with hyphen/region
        assert disposition("attachment; filename*=UTF-8'en-US'doc%20(1).pdf") == "doc (1).pdf"
        # Empty filename* data falls back to None
        assert disposition("attachment; filename*=UTF-8''") is None

    def test_rfc5987_precedence_over_filename(self):
        header = "attachment; filename=\"fallback.txt\"; filename*=UTF-8''preferred.txt"
        assert disposition(header) == "preferred.txt"

    def test_rfc5987_fallback_on_unrecognized_format(self):
        header = 'attachment; filename="fallback.txt"; filename*="unrecognized_format"'
        assert disposition(header) == "fallback.txt"

    def test_rfc5987_errors(self):
        with pytest.raises(ValueError, match="Content-Disposition:"):
            disposition("attachment; filename*=unknown-charset''%66ile.txt")

        with pytest.raises(ValueError, match="Content-Disposition:"):
            disposition("attachment; filename*=UTF-8''%FF%FE.txt")

    def test_rfc2047_encoded_filename(self):
        # RFC 2047 Base64 in filename
        assert disposition('attachment; filename="=?UTF-8?B?dGVzdC50eHQ=?="') == "test.txt"
        # RFC 2047 Quoted-Printable in filename
        assert disposition('attachment; filename="=?ISO-8859-1?Q?hello_world.txt?="') == "hello world.txt"
        # RFC 2047 case-insensitivity
        assert disposition('attachment; filename="=?utf-8?b?dGVzdC50eHQ=?="') == "test.txt"
        # RFC 2047 in filename*
        assert disposition('attachment; filename*="=?UTF-8?B?dGVzdC50eHQ=?="') == "test.txt"

    def test_rfc2047_extended_edge_cases(self):
        # Quoted-Printable with hex escapes (=C3=A9 = é)
        assert disposition('attachment; filename="=?utf-8?q?caf=C3=A9.txt?="') == "café.txt"
        # Base64 with padding
        assert disposition('attachment; filename="=?utf-8?b?Zm9vLnR4dA==?="') == "foo.txt"

    def test_rfc2047_errors(self):
        with pytest.raises(ValueError, match="Content-Disposition:"):
            disposition('attachment; filename="=?unknown-enc?B?dGVzdA==?="')

        with pytest.raises(ValueError, match="Content-Disposition:"):
            disposition('attachment; filename*="=?unknown-enc?B?dGVzdA==?="')

    def test_url_encoded_and_unicode_filename(self):
        assert disposition('attachment; filename="%E6%B5%8B%E8%AF%95.txt"') == "测试.txt"
        assert disposition('attachment; filename="%E9cole.txt"') == "école.txt"
        assert disposition('attachment; filename="€uro.pdf"') == "€uro.pdf"
        # Raw UTF-8 bytes as received from HTTP header (decoded as ISO-8859-1)
        latin1_header = 'attachment; filename="\xd0\xb4\xd0\xbe\xd0\xba\xd1\x83\xd0\xbc\xd0\xb5\xd0\xbd\xd1\x82_2025.pdf"'
        assert disposition(latin1_header) == "документ_2025.pdf"

    def test_unicode_and_charset_fallback_edge_cases(self):
        # ISO-8859-1 percent-encoding (%FC = ü in Latin-1, invalid start byte in UTF-8)
        assert disposition('attachment; filename="%FCber.txt"') == "über.txt"
        # Literal multi-byte CJK characters in unencoded filename
        assert disposition('attachment; filename="日本語.txt"') == "日本語.txt"
        # Literal emoji characters
        assert disposition('attachment; filename="📁notes.txt"') == "📁notes.txt"

    def test_attachment_fallback(self):
        assert disposition("attachment", location="http://example.com/files/download.zip") == "download.zip"
        assert disposition("attachment", fallback_url="http://example.com/files/backup.tar") == "backup.tar"
        assert disposition(
            "attachment",
            location="http://example.com/files/download.zip",
            fallback_url="http://example.com/files/backup.tar",
        ) == "download.zip"
        assert disposition(
            'attachment; filename="explicit.txt"',
            location="http://example.com/files/download.zip",
            fallback_url="http://example.com/files/backup.tar",
        ) == "explicit.txt"
        assert disposition("ATTACHMENT", location="http://example.com/files/download.zip") == "download.zip"
        # Non-attachment disposition type does not trigger fallback
        assert disposition("inline", location="http://example.com/files/download.zip") is None

    def test_attachment_fallback_url_edge_cases(self):
        # Fallback URL with query string
        assert disposition("attachment", fallback_url="http://example.com/get?id=123&name=my_archive.zip") == "get"
        # Fallback URL with fragment
        assert disposition("attachment", fallback_url="http://example.com/page.html#file_version_2") == "page.html#file_version_2"
        # Unknown/custom disposition type does not trigger fallback
        assert disposition("custom-disp", location="http://example.com/download.zip") is None

    def test_sanitization(self):
        assert disposition('attachment; filename="../../../etc/passwd"') == "passwd"
        assert disposition(r'attachment; filename="..\..\windows\calc.exe"') == "calc.exe"
        assert disposition('attachment; filename="/var/log/syslog"') == "syslog"
        assert disposition(r'attachment; filename="C:\secret\keys.txt"') == "keys.txt"
        assert disposition('attachment; filename=".hidden.txt"') == "hidden.txt"
        assert disposition('attachment; filename="...archive.tar.gz"') == "archive.tar.gz"
        assert disposition('attachment; filename="report<1>|2*3?4.txt"') == "report_1__2_3_4.txt"
        assert disposition('attachment; filename="CON"') == "_CON"
        assert disposition('attachment; filename="prn"') == "_prn"

    def test_sanitization_extended_edge_cases(self):
        # Mixed POSIX and Windows slashes
        assert disposition(r'attachment; filename="/foo/bar\\baz/test.txt"') == "test.txt"
        # Relative path dot components
        assert disposition('attachment; filename="folder/subfolder/./../target.txt"') == "target.txt"
        # Windows drive letter paths
        assert disposition(r'attachment; filename="D:\music\song.mp3"') == "song.mp3"
        assert disposition('attachment; filename="D:song.mp3"') == "song.mp3"
        # Additional Windows reserved device names
        assert disposition('attachment; filename="lpt1"') == "_lpt1"
        assert disposition('attachment; filename="com9"') == "_com9"
        assert disposition('attachment; filename="COM1"') == "_COM1"
        # Windows reserved name with extension is not treated as device name
        assert disposition('attachment; filename="com1.tar.gz"') == "com1.tar.gz"
        # Null bytes removed
        assert disposition('attachment; filename="null\x00byte.txt"') == "nullbyte.txt"
        # Leading and trailing spaces trimmed
        assert disposition('attachment; filename="   name   "') == "name"

    def test_none_and_empty_values(self):
        assert disposition("") is None
        assert disposition("attachment") is None
        assert disposition('attachment; filename=""') is None
        assert disposition('attachment; filename="   "') == ""
        assert disposition('attachment; filename="."') == ""
        assert disposition('attachment; filename=".."') == ""
        assert disposition('attachment; filename="..."') == ""
        assert disposition('attachment; filename="...."') == ""
        assert disposition("attachment; size=1024") is None
        assert disposition("inline") is None


