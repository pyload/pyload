"""
Unit tests for CWE-409 (Improper Handling of Highly Compressed Data / Decompression Bombs)
protection across pyLoad extractors and ExtractArchive addon.
"""
import io
import os
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pyload.plugins.base.extractor import ArchiveError, BaseExtractor, PasswordError
from pyload.plugins.extractors.UnZip import UnZip
from pyload.plugins.extractors.UnTar import UnTar
from pyload.plugins.extractors.SevenZip import SevenZip
from pyload.plugins.extractors.UnRar import UnRar
from pyload.plugins.extractors.HjSplit import HjSplit
from pyload.plugins.addons.ExtractArchive import ExtractArchive


class TestBaseExtractorFreeSpace(unittest.TestCase):
    """Test suite for BaseExtractor free space validation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 1024  # 1024 MiB default min_free_space

        self.extractor = BaseExtractor(
            pyfile=self.mock_pyfile,
            filename="test.zip",
            out=self.temp_dir,
            fullpath=True,
            overwrite=False,
            excludefiles=None,
            priority=0,
            keepbroken=False,
        )

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_sufficient_free_space_passes(self):
        """Extraction should proceed when free space exceeds required + min_free_space."""
        # 10 GB available, 1 GB min_free_space -> 9 GB usable. Requesting 100 MB.
        self.mock_core.config.get.return_value = 1024
        with patch.object(self.extractor, '_get_free_space', return_value=10 * 1024 * 1024 * 1024):
            # Should not raise
            self.extractor._check_free_space(100 * 1024 * 1024)

    def test_insufficient_free_space_raises_archive_error(self):
        """Extraction should raise ArchiveError when required size exceeds available space."""
        # 2 GB available, 1 GB min_free_space -> 1 GB usable. Requesting 2 GB.
        self.mock_core.config.get.return_value = 1024
        with patch.object(self.extractor, '_get_free_space', return_value=2 * 1024 * 1024 * 1024):
            with self.assertRaises(ArchiveError) as ctx:
                self.extractor._check_free_space(2 * 1024 * 1024 * 1024)
            self.assertIn("Insufficient disk space", str(ctx.exception))

    def test_disk_below_min_free_space_raises_archive_error(self):
        """Extraction should raise ArchiveError if available space is already below min_free_space."""
        # 500 MB available, 1024 MB min_free_space -> usable is -524 MB.
        self.mock_core.config.get.return_value = 1024
        with patch.object(self.extractor, '_get_free_space', return_value=500 * 1024 * 1024):
            with self.assertRaises(ArchiveError) as ctx:
                self.extractor._check_free_space(0)
            self.assertIn("Insufficient disk space", str(ctx.exception))

    def test_unknown_free_space_does_not_block(self):
        """If free space cannot be determined, check should not raise error."""
        with patch.object(self.extractor, '_get_free_space', return_value=None):
            # Should not raise
            self.extractor._check_free_space(10 * 1024 * 1024 * 1024)


class TestUnZipDecompressionBombProtection(unittest.TestCase):
    """Test suite for UnZip decompression bomb mitigations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.archive_path = os.path.join(self.temp_dir, "test.zip")
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 0  # 0 min_free_space for simplicity

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_unzip_extract_rejects_bomb_exceeding_free_space(self):
        """UnZip.extract should reject archive when uncompressed file size exceeds free space."""
        with zipfile.ZipFile(self.archive_path, "w") as z:
            z.writestr("huge_file.bin", b"test")

        unzip = UnZip(self.mock_pyfile, self.archive_path, self.temp_dir)

        # Mock free space to 2 bytes, but file claims 4 bytes
        with patch.object(unzip, '_get_free_space', return_value=2):
            with self.assertRaises(ArchiveError) as ctx:
                unzip.extract()
            self.assertIn("Insufficient disk space", str(ctx.exception))

    def test_unzip_extract_does_not_call_verify_password(self):
        """UnZip.extract should NOT call self.verify_password() to avoid redundant full decompressions."""
        with zipfile.ZipFile(self.archive_path, "w") as z:
            z.writestr("file.txt", b"hello world")

        unzip = UnZip(self.mock_pyfile, self.archive_path, self.temp_dir)

        with patch.object(unzip, 'verify_password') as mock_verify:
            extracted = unzip.extract()
            mock_verify.assert_not_called()
            self.assertEqual(len(extracted), 1)

    def test_unzip_extract_considers_excludefiles_for_free_space_check(self):
        """UnZip.extract must exclude files matching self.excludefiles from free space check."""
        with zipfile.ZipFile(self.archive_path, "w") as z:
            z.writestr("movie.iso", b"0" * 5000)
            z.writestr("readme.txt", b"0" * 2000)

        unzip = UnZip(
            self.mock_pyfile,
            self.archive_path,
            self.temp_dir,
            excludefiles=["*.iso"],
        )

        with patch.object(unzip, "_check_free_space") as mock_check_space:
            unzip.extract()
            # movie.iso (5000) should be excluded: required size is 2000
            mock_check_space.assert_called_with(2000)

    @patch('pyload.plugins.extractors.UnZip.zipfile.ZipFile')
    def test_unzip_verify_fast_probes_encrypted_archive(self, mock_zipfile_cls):
        """UnZip.verify_password should probe only smallest file on password protected archive."""
        mock_z = MagicMock()
        mock_info_large = MagicMock(filename="large.bin", file_size=10000, flag_bits=1, is_dir=lambda: False)
        mock_info_small = MagicMock(filename="small.bin", file_size=10, flag_bits=1, is_dir=lambda: False)
        mock_z.infolist.return_value = [mock_info_large, mock_info_small]
        mock_z.namelist.return_value = ["large.bin", "small.bin"]

        def mock_open(name):
            if mock_z.setpassword.call_args and mock_z.setpassword.call_args[0][0] == b"wrong":
                raise RuntimeError("Bad password")
            return io.BytesIO(b"data")

        mock_z.open.side_effect = mock_open
        mock_zipfile_cls.return_value.__enter__.return_value = mock_z

        unzip = UnZip(self.mock_pyfile, "test.zip", self.temp_dir)

        # No password -> PasswordError
        with self.assertRaises(PasswordError):
            unzip.verify_password(password=None)

        # Wrong password -> PasswordError
        with self.assertRaises(PasswordError):
            unzip.verify_password(password="wrong")

        # Correct password -> succeeds and opens smallest member
        unzip.verify_password(password="secret")
        mock_z.open.assert_called_with("small.bin")


class TestSevenZipDecompressionBombProtection(unittest.TestCase):
    """Test suite for SevenZip extractor size validation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 0

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_7zip_extract_rejects_when_size_exceeds_free_space(self):
        """SevenZip.extract should validate Σ archive_info[].size against free space."""
        sevenzp = SevenZip(self.mock_pyfile, "test.7z", self.temp_dir)

        fake_archive_info = [
            {"path": "file1.bin", "full_path": os.path.join(self.temp_dir, "file1.bin"), "size": 10 * 1024 * 1024 * 1024, "attributes": "...."},
        ]

        with patch.object(sevenzp, '_get_archive_info', return_value=fake_archive_info):
            with patch.object(sevenzp, '_detect_7zip_symlinks'):
                with patch.object(sevenzp, '_get_free_space', return_value=5 * 1024 * 1024 * 1024):
                    with patch.object(sevenzp, 'call_cmd') as mock_call:
                        with self.assertRaises(ArchiveError) as ctx:
                            sevenzp.extract(password=None)
                        self.assertIn("Insufficient disk space", str(ctx.exception))
                        # Ensure extraction command was NEVER executed
                        mock_call.assert_not_called()

    def test_7zip_extract_considers_excludefiles_for_free_space_check(self):
        """SevenZip.extract must exclude files matching self.excludefiles from free space check."""
        sevenzp = SevenZip(
            self.mock_pyfile,
            "test.7z",
            self.temp_dir,
            excludefiles=["*.iso"],
        )

        fake_archive_info = [
            {"path": "movie.iso", "full_path": os.path.join(self.temp_dir, "movie.iso"), "size": 5000000, "attributes": "...."},
            {"path": "readme.txt", "full_path": os.path.join(self.temp_dir, "readme.txt"), "size": 2000, "attributes": "...."},
        ]

        with patch.object(sevenzp, '_get_archive_info', return_value=fake_archive_info):
            with patch.object(sevenzp, '_detect_7zip_symlinks'):
                with patch.object(sevenzp, '_validate_extracted_symlinks'):
                    with patch.object(sevenzp, 'call_cmd') as mock_call:
                        mock_proc = MagicMock()
                        mock_proc.communicate.return_value = ("", "")
                        mock_proc.returncode = 0
                        mock_proc.stdout.read.return_value = ""
                        mock_call.return_value = mock_proc

                        with patch.object(sevenzp, '_check_free_space') as mock_check_space:
                            sevenzp.extract(password=None)
                            # movie.iso (5000000) should be excluded: required size is 2000
                            mock_check_space.assert_called_with(2000)


class TestUnTarDecompressionBombProtection(unittest.TestCase):
    """Test suite for UnTar extractor size cap."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.archive_path = os.path.join(self.temp_dir, "test.tar")
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 0

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_untar_extract_rejects_when_uncompressed_size_exceeds_free_space(self):
        """UnTar.extract should check member sizes against free space before extracting."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            data = b"x" * 1000
            f = tarfile.TarInfo("bomb.bin")
            f.size = len(data)
            tar.addfile(f, io.BytesIO(data))

        tar_buffer.seek(0)
        with open(self.archive_path, "wb") as f:
            f.write(tar_buffer.getvalue())

        untar = UnTar(self.mock_pyfile, self.archive_path, self.temp_dir)

        # 500 bytes available space, but file is 1000 bytes
        with patch.object(untar, '_get_free_space', return_value=500):
            with patch.object(untar, '_safe_extractall') as mock_extractall:
                with self.assertRaises(ArchiveError) as ctx:
                    untar.extract()
                self.assertIn("Insufficient disk space", str(ctx.exception))
                mock_extractall.assert_not_called()

    def test_untar_extract_considers_excludefiles_for_free_space_check(self):
        """UnTar.extract must exclude files matching self.excludefiles from free space check."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            data1 = b"0" * 5000
            f1 = tarfile.TarInfo("movie.iso")
            f1.size = len(data1)
            tar.addfile(f1, io.BytesIO(data1))

            data2 = b"0" * 2000
            f2 = tarfile.TarInfo("readme.txt")
            f2.size = len(data2)
            tar.addfile(f2, io.BytesIO(data2))

        tar_buffer.seek(0)
        with open(self.archive_path, "wb") as f:
            f.write(tar_buffer.getvalue())

        untar = UnTar(
            self.mock_pyfile,
            self.archive_path,
            self.temp_dir,
            excludefiles=["*.iso"],
        )

        with patch.object(untar, 'verify_password'):
            with patch.object(untar, '_safe_extractall'):
                with patch.object(untar, '_check_free_space') as mock_check_space:
                    untar.extract()
                    # movie.iso (5000) should be excluded: required size is 2000
                    mock_check_space.assert_called_with(2000)


class TestUnRarDecompressionBombProtection(unittest.TestCase):
    """Test suite for UnRar extractor size validation and exclusion handling."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 0

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_unrar_extract_considers_excludefiles_for_free_space_check(self):
        """UnRar.extract must exclude files matching self.excludefiles from free space check."""
        sample_output = (
            "Attributes      Size        Date       Time    Name\n"
            "---------------------------------------------------\n"
            " ...A...       5000000       2026-01-01 12:00  movie.iso\n"
            " ...A...          2000       2026-01-01 12:00  readme.txt\n"
            " ...A...          1000       2026-01-01 12:00  small.nfo\n"
        )
        unrar = UnRar(
            self.mock_pyfile,
            "test.rar",
            self.temp_dir,
            excludefiles=["*.iso"],
        )
        unrar.VERSION = "5.0"
        unrar._RE_FILES = unrar._RE_FILES_V5

        mock_proc_list = MagicMock()
        mock_proc_list.communicate.return_value = (sample_output, "")
        mock_proc_list.returncode = 0

        mock_proc_extract = MagicMock()
        mock_proc_extract.communicate.return_value = ("", "")
        mock_proc_extract.returncode = 0
        mock_proc_extract.stdout.read.return_value = ""

        with patch.object(unrar, "call_cmd", side_effect=[mock_proc_list, mock_proc_extract]):
            with patch.object(unrar, "_check_free_space") as mock_check_space:
                unrar.extract()
                # movie.iso (5000000) should be excluded: 2000 + 1000 = 3000
                mock_check_space.assert_called_with(3000)

    def test_unrar_extract_recalculates_total_size_with_updated_excludefiles(self):
        """UnRar.extract must recalculate remaining size when excludefiles is updated."""
        sample_output = (
            "Attributes      Size        Date       Time    Name\n"
            "---------------------------------------------------\n"
            " ...A...          3000       2026-01-01 12:00  file1.txt\n"
            " ...A...          2000       2026-01-01 12:00  file2.txt\n"
            " ...A...          1000       2026-01-01 12:00  small.nfo\n"
        )
        unrar = UnRar(
            self.mock_pyfile,
            "test.rar",
            self.temp_dir,
        )
        unrar.VERSION = "5.0"
        unrar._RE_FILES = unrar._RE_FILES_V5

        mock_proc_list = MagicMock()
        mock_proc_list.communicate.return_value = (sample_output, "")
        mock_proc_list.returncode = 0

        mock_proc_extract = MagicMock()
        mock_proc_extract.communicate.return_value = ("", "")
        mock_proc_extract.returncode = 0
        mock_proc_extract.stdout.read.return_value = ""

        with patch.object(unrar, "call_cmd", side_effect=[mock_proc_list, mock_proc_extract]):
            unrar._find_smallest_file()

            # Simulate verify_password() appending small.nfo to excludefiles after testing password
            unrar.excludefiles.append("small.nfo")

            with patch.object(unrar, "_check_free_space") as mock_check_space:
                unrar.extract()
                # Required size must be recalculated without small.nfo (3000 + 2000 = 5000)
                mock_check_space.assert_called_with(5000)

    def test_unrar_extract_single_file_probes_only_file_size(self):
        """UnRar.extract(file=...) must check free space for only the specified file."""
        sample_output = (
            "Attributes      Size        Date       Time    Name\n"
            "---------------------------------------------------\n"
            " ...A...       5000000       2026-01-01 12:00  large.bin\n"
            " ...A...          1000       2026-01-01 12:00  small.nfo\n"
        )
        unrar = UnRar(
            self.mock_pyfile,
            "test.rar",
            self.temp_dir,
        )
        unrar.VERSION = "5.0"
        unrar._RE_FILES = unrar._RE_FILES_V5

        mock_proc_list = MagicMock()
        mock_proc_list.communicate.return_value = (sample_output, "")
        mock_proc_list.returncode = 0

        mock_proc_extract = MagicMock()
        mock_proc_extract.communicate.return_value = ("", "")
        mock_proc_extract.returncode = 0
        mock_proc_extract.stdout.read.return_value = ""

        with patch.object(unrar, "call_cmd", side_effect=[mock_proc_list, mock_proc_extract]):
            with patch.object(unrar, "_check_free_space") as mock_check_space:
                unrar.extract(file="small.nfo")
                mock_check_space.assert_called_with(1000)

    def test_unrar_extract_rejects_when_total_size_exceeds_free_space(self):
        """UnRar.extract must reject extraction when total_size exceeds available disk space."""
        sample_output = (
            "Attributes      Size        Date       Time    Name\n"
            "---------------------------------------------------\n"
            " ...A...       5000000       2026-01-01 12:00  huge_bomb.bin\n"
        )
        unrar = UnRar(
            self.mock_pyfile,
            "test.rar",
            self.temp_dir,
        )
        unrar.VERSION = "5.0"
        unrar._RE_FILES = unrar._RE_FILES_V5

        mock_proc_list = MagicMock()
        mock_proc_list.communicate.return_value = (sample_output, "")
        mock_proc_list.returncode = 0

        with patch.object(unrar, "call_cmd", return_value=mock_proc_list):
            with patch.object(unrar, "_get_free_space", return_value=1000):
                with self.assertRaises(ArchiveError) as ctx:
                    unrar.extract()
                self.assertIn("Insufficient disk space", str(ctx.exception))


class TestHjSplitDecompressionBombProtection(unittest.TestCase):
    """Test suite for HjSplit merge size bounds check."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_pyfile = MagicMock()
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_pyfile.m.pyload = self.mock_core
        self.mock_core.config.get.return_value = 0

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_hjsplit_extract_rejects_when_total_size_exceeds_free_space(self):
        """HjSplit.extract should validate size_total against free space before writing."""
        part1 = os.path.join(self.temp_dir, "file.bin.001")
        part2 = os.path.join(self.temp_dir, "file.bin.002")

        with open(part1, "wb") as f:
            f.write(b"a" * 1000)
        with open(part2, "wb") as f:
            f.write(b"b" * 1000)

        hjsplit = HjSplit(self.mock_pyfile, part1, self.temp_dir)
        with patch.object(hjsplit, 'chunks', return_value=[part1, part2]):
            # Only 500 bytes available
            with patch.object(hjsplit, '_get_free_space', return_value=500):
                with self.assertRaises(ArchiveError) as ctx:
                    hjsplit.extract()
                self.assertIn("Insufficient disk space", str(ctx.exception))
                # Output file was not created
                self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "file.bin")))


class TestExtractArchiveRecursionAndQuotas(unittest.TestCase):
    """Test suite for ExtractArchive recursive depth limits and quotas."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.password_file = os.path.join(self.temp_dir, "passwords.txt")
        self.mock_core = MagicMock()
        self.mock_core.debug = 0
        self.mock_manager = MagicMock()
        self.mock_core.config.get.side_effect = lambda cat, opt: {
            ("general", "storage_folder"): self.temp_dir,
            ("general", "min_free_space"): 1024,
            ("general", "folder_per_package"): False,
        }.get((cat, opt), None)

        self.addon = ExtractArchive(self.mock_core, self.mock_manager)
        self.addon.queue = MagicMock()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_default_config_includes_max_depth_and_max_extracted_size(self):
        """ExtractArchive configuration must define max_depth and max_extracted_size."""
        config_names = [opt[0] for opt in ExtractArchive.__config__]
        self.assertIn("max_depth", config_names)
        self.assertIn("max_extracted_size", config_names)

    def test_extract_stops_when_max_depth_reached(self):
        """ExtractArchive.extract must not recurse deeper than max_depth."""
        mock_pypack = MagicMock()
        mock_pypack.id = 1
        mock_pypack.name = "test_pkg"
        mock_pypack.folder = ""
        mock_pypack.password = ""
        mock_pypack.get_children.return_value = {
            "root.zip": {"id": 10, "name": "root.zip"}
        }

        self.mock_core.files.get_package.return_value = mock_pypack
        self.addon.config = MagicMock()
        self.addon.config.get.side_effect = lambda opt, default=None: {
            "destination": "",
            "subfolder": False,
            "fullpath": True,
            "overwrite": False,
            "priority": 0,
            "recursive": True,
            "max_depth": 2,
            "max_extracted_size": 0,
            "keepbroken": False,
            "extensions": "zip",
            "excludefiles": "",
            "delete": False,
            "passwordfile": self.password_file,
            "usepasswordfile": False,
        }.get(opt, default)

        mock_extractor_cls = MagicMock()
        mock_extractor_cls.__name__ = "MockExtractor"
        mock_extractor_cls.archivetype.return_value = "zip"

        layer_count = [0]
        def mock_get_targets(files_ids):
            targets = []
            for fid, fname, fout in files_ids:
                targets.append((fid, fname, fout))
            return targets

        mock_extractor_cls.get_targets.side_effect = mock_get_targets

        def mock_extract(pyfile, archive, password):
            layer_count[0] += 1
            nested_name = f"nested_layer_{layer_count[0]}.zip"
            nested_path = os.path.join(self.temp_dir, nested_name)
            # Create the file so os.path.isfile is True
            with open(nested_path, "w") as f:
                f.write("data")
            return [nested_path]

        self.addon.extractors = [mock_extractor_cls]
        self.addon._extract = MagicMock(side_effect=mock_extract)

        root_zip = os.path.join(self.temp_dir, "root.zip")
        with open(root_zip, "w") as f:
            f.write("root")

        mock_thread = MagicMock()
        self.addon.extract([1], mock_thread)

        # With max_depth=2:
        # Depth 0: extracts root.zip (produces nested_layer_1.zip)
        # Depth 1: extracts nested_layer_1.zip (produces nested_layer_2.zip)
        # Depth 2: extracts nested_layer_2.zip (produces nested_layer_3.zip)
        # Depth 3: skipped because current_depth + 1 > max_depth!
        # Total extraction invocations should be 3 (depth 0, 1, 2)
        self.assertEqual(self.addon._extract.call_count, 3)

    def test_extract_stops_when_aggregate_size_quota_exceeded(self):
        """ExtractArchive.extract must stop when aggregate extracted bytes exceed quota."""
        mock_pypack = MagicMock()
        mock_pypack.id = 1
        mock_pypack.name = "test_pkg"
        mock_pypack.folder = ""
        mock_pypack.password = ""
        mock_pypack.get_children.return_value = {
            "root.zip": {"id": 10, "name": "root.zip"}
        }

        self.mock_core.files.get_package.return_value = mock_pypack
        self.addon.config = MagicMock()
        self.addon.config.get.side_effect = lambda opt, default=None: {
            "destination": "",
            "subfolder": False,
            "fullpath": True,
            "overwrite": False,
            "priority": 0,
            "recursive": True,
            "max_depth": 10,
            "max_extracted_size": 1,  # 1 MiB quota
            "keepbroken": False,
            "extensions": "zip",
            "excludefiles": "",
            "delete": False,
            "passwordfile": self.password_file,
            "usepasswordfile": False,
        }.get(opt, default)

        mock_extractor_cls = MagicMock()
        mock_extractor_cls.__name__ = "MockExtractor"
        mock_extractor_cls.archivetype.return_value = "zip"
        mock_extractor_cls.get_targets.side_effect = lambda files_ids: [(fid, fname, fout) for fid, fname, fout in files_ids]

        # First extraction writes a 2 MB file (exceeding 1 MB quota)
        def mock_extract(pyfile, archive, password):
            extracted_path = os.path.join(self.temp_dir, "large.bin")
            with open(extracted_path, "wb") as f:
                f.write(b"0" * (2 * 1024 * 1024))
            return [extracted_path]

        self.addon.extractors = [mock_extractor_cls]
        self.addon._extract = MagicMock(side_effect=mock_extract)

        root_zip = os.path.join(self.temp_dir, "root.zip")
        with open(root_zip, "w") as f:
            f.write("root")

        mock_thread = MagicMock()
        result = self.addon.extract([1], mock_thread)
        # Should fail extraction due to quota exceeded
        self.assertFalse(result)
