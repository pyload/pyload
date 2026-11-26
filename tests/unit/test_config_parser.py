import os
import tempfile
import pytest

from pyload.core.config.parser import ConfigParser


class TestConfigParserCast:
    @pytest.fixture
    def parser(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ConfigParser(tmpdir)

    def test_cast_str_valid(self, parser):
        assert parser.cast("str", "valid_string") == "valid_string"
        assert parser.cast("str", "") == ""
        assert parser.cast("str", None) == ""

    def test_cast_str_rejects_newlines(self, parser):
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("str", "hello\nworld")
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("str", "hello\rworld")
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("str", "hello\r\nworld")
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("str", "hello\0world")

    def test_cast_unlisted_types_reject_newlines(self, parser):
        # Unlisted metadata type annotations (e.g. password, ip) fall through to else:
        assert parser.cast("password", "safe_pass") == "safe_pass"
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("password", "pass\ninjection")
        assert parser.cast("ip", "127.0.0.1") == "127.0.0.1"
        assert parser.cast("ip", "localhost") == "localhost"
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("ip", "127.0.0.1\nreconnect - \"Reconnection\":")

    def test_cast_file_folder_rejects_newlines(self, parser):
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("folder", "/tmp/evil\nscript=foo")
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("file", "/tmp/evil.sh\ninjected=1")

    def test_cast_bytes_rejects_newlines(self, parser):
        assert parser.cast("bytes", b"safe") == b"safe"
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast("bytes", b"evil\ninjection")

    def test_cast_choice_string_rejects_newlines_and_injections(self, parser):
        typ = "modern;pyplex"
        assert parser.cast(typ, "modern") == "modern"
        assert parser.cast(typ, "pyplex") == "pyplex"
        injection = "modern\ngeneral - \"General\":\n\tfolder storage_folder : \"Injected\" = /tmp/evil\n"
        with pytest.raises(ValueError, match="newline or control characters"):
            parser.cast(typ, injection)


class TestConfigParserSerialization:
    def test_save_config_sanitizes_newlines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = ConfigParser(tmpdir)
            cfg_file = os.path.join(tmpdir, "test.cfg")

            # Force dangerous entries directly into dictionary
            fake_config = {
                "webui\ninjected_sec": {
                    "desc": "Web UI\ninjected_desc",
                    "theme": {
                        "type": "modern;pyplex\ninjected_type",
                        "desc": "Theme\ninjected_desc",
                        "value": "modern\ngeneral - \"General\":\n\tfolder storage_folder = /tmp/evil\n"
                    }
                }
            }
            parser.save_config(fake_config, cfg_file)

            with open(cfg_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Verify no line starts with general section or injected option
            for line in lines:
                assert not line.strip().startswith('general - "General":')
                assert not line.strip().startswith('folder storage_folder')

            # And when parsed, general was never created as a section
            parsed = parser.parse_config(cfg_file)
            assert "general" not in parsed

    def test_parse_config_with_escaped_quotes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = ConfigParser(tmpdir)
            cfg_file = os.path.join(tmpdir, "test_escaped.cfg")

            content = (
                "version: 1\n"
                "general - \"General\":\n"
                "\tstr simple : \"Option with \\\"quotes\\\" inside\" = hello\n"
                "\tstr tricky : \"Option with \\\" = \\\" separator\" = world\n"
                "\tint number : \"Number with \\\"quoted desc\\\"\" = 42\n"
            )
            with open(cfg_file, "w", encoding="utf-8") as f:
                f.write(content)

            parsed = parser.parse_config(cfg_file)
            assert parsed["general"]["simple"]["desc"] == 'Option with "quotes" inside'
            assert parsed["general"]["simple"]["value"] == "hello"

            assert parsed["general"]["tricky"]["desc"] == 'Option with " = " separator'
            assert parsed["general"]["tricky"]["value"] == "world"

            assert parsed["general"]["number"]["desc"] == 'Number with "quoted desc"'
            assert parsed["general"]["number"]["value"] == 42

    def test_roundtrip_escaped_quotes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = ConfigParser(tmpdir)
            cfg_file = os.path.join(tmpdir, "test_roundtrip.cfg")

            original_config = {
                "general": {
                    "desc": "General settings",
                    "my_opt": {
                        "type": "str",
                        "desc": 'Option with "embedded" quotes and "another"',
                        "value": "my_val",
                    },
                }
            }
            parser.save_config(original_config, cfg_file)

            with open(cfg_file, "r", encoding="utf-8") as f:
                file_text = f.read()

            # Ensure quotes were escaped in the written file
            assert r'\"embedded\"' in file_text
            assert r'\"another\"' in file_text

            parsed = parser.parse_config(cfg_file)
            assert (
                parsed["general"]["my_opt"]["desc"]
                == 'Option with "embedded" quotes and "another"'
            )
            assert parsed["general"]["my_opt"]["value"] == "my_val"


class TestApiSetConfigSecurity:
    def test_set_config_value_crlf_rejection(self, monkeypatch):
        from pyload.core.api import Api
        from unittest.mock import MagicMock

        mock_pyload = MagicMock()
        mock_pyload.log = MagicMock()

        api = Api(mock_pyload)
        # Attempt newline injection
        api.set_config_value("webui", "theme", "modern\ngeneral - \"General\":\n", section="core")

        # mock_pyload.config.set should not have been called
        mock_pyload.config.set.assert_not_called()
        mock_pyload.log.error.assert_called()
