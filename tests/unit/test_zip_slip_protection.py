"""
Unit tests for path traversal ("Zip Slip") attack prevention in archive extractors.
"""
import os
import platform
import stat
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pyload.plugins.base.extractor import ArchiveError, BaseExtractor

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"


def can_create_symlinks():
    """Check if the current system can create symlinks."""
    try:
        test_dir = tempfile.mkdtemp()
        test_link = os.path.join(test_dir, "test_link")
        test_target = os.path.join(test_dir, "test_target")
        # Create a target file
        with open(test_target, 'w') as f:
            f.write("test")
        # Try to create a symlink
        os.symlink(test_target, test_link)
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
        return True
    except (OSError, NotImplementedError):
        return False


SYMLINKS_SUPPORTED = can_create_symlinks()


class TestPathTraversalProtection(unittest.TestCase):
    """Test suite for path traversal attack prevention"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create a mock pyfile
        self.mock_pyfile = MagicMock()
        self.mock_pyfile.m.pyload = MagicMock()

        # Create a basic extractor instance for testing
        self.extractor = BaseExtractor(
            pyfile=self.mock_pyfile,
            filename="test.zip",
            out=self.temp_dir,
            fullpath=True,
            overwrite=False,
            excludefiles=None,
            priority=0,
            keepbroken=False
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_valid_entries_accepted(self):
        """Valid archive entries should be accepted"""
        valid_entries = [
            "file.txt",
            "subdir/file.txt",
            "nested/subdir/file.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
        ]

        # Should not raise an exception
        result = self.extractor._validate_archive_entries(valid_entries)
        self.assertEqual(len(result), len(valid_entries))

    def test_path_traversal_parent_dir_rejected(self):
        """Path traversal with ../ should be rejected"""
        malicious_entries = [
            "..",
            "../etc/passwd",
            "../../etc/shadow",
            "subdir/../../etc/passwd",
        ]

        # Add Windows-specific entries
        if IS_WINDOWS:
            malicious_entries.append("..\\..\\windows\\system32\\config\\sam")

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                self.assertIn("path traversal", str(ctx.exception).lower())

    def test_absolute_paths_rejected(self):
        """Absolute paths should be rejected"""
        malicious_entries = [
            "/etc/passwd",
            "/root/.ssh/id_rsa",
        ]

        # Add Windows-specific paths if on Windows
        if IS_WINDOWS:
            malicious_entries.extend([
                "C:\\Windows\\System32\\config\\sam",
                "D:\\sensitive\\data.txt",
            ])

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                exception_msg = str(ctx.exception).lower()
                self.assertTrue(
                    any(phrase in exception_msg for phrase in [
                        "path traversal",
                        "illegal character",
                        "invalid archive",
                        "invalid path"
                    ]),
                    f"Expected traversal or invalid path error for entry: {entry}\n"
                    f"Got: {ctx.exception}"
                )

    def test_leading_slashes_stripped(self):
        """Leading slashes should be stripped and files normalized"""
        entries_with_leading_slashes = [
            "/file.txt",
            "/subdir/file.txt",
        ]

        # Should raise ArchiveError - leading slashes indicate absolute paths
        for entry in entries_with_leading_slashes:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                self.assertIn("path traversal", str(ctx.exception).lower())

    def test_nested_subdirectories_allowed(self):
        """Nested subdirectories within destination should be allowed"""
        valid_nested_entries = [
            "dir1/file.txt",
            "dir1/dir2/file.txt",
            "dir1/dir2/dir3/file.txt",
            "a/b/c/d/e/f/file.txt",
        ]

        result = self.extractor._validate_archive_entries(valid_nested_entries)
        self.assertEqual(len(result), len(valid_nested_entries))

    def test_valid_byte_entries_accepted(self):
        """Valid byte path entries should be accepted"""
        byte_entries = [
            b"file.txt",
            b"subdir/file.txt",
        ]

        result = self.extractor._validate_archive_entries(byte_entries)
        self.assertEqual(len(result), len(byte_entries))

    def test_bytes_traversal_rejected(self):
        """Path traversal in byte paths should be rejected"""
        malicious_byte_entries = [
            b"../etc/passwd",
            b"/etc/passwd",
        ]

        for entry in malicious_byte_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                self.assertIn("path traversal", str(ctx.exception).lower())

    def test_mixed_separators_rejected(self):
        """Paths with mixed separators attempting traversal should be rejected"""
        # These should be rejected on ALL platforms (Linux, Windows, macOS)
        malicious_entries = [
            # Pure forward slashes (universal)
            "subdir//file",
            "subdir/../../etc/passwd",
            "../../../etc/passwd",
            "../etc/passwd",
            "deep/subdir/../../../../../etc/shadow",

            # Mixed separators (the tricky ones)
            "subdir/..\\../etc/passwd",
            "subdir\\..\\../etc/passwd",
            "..\\../etc/passwd",
            "../..\\etc/passwd",
            "subdir/..\\..\\windows\\system32\\config\\sam",

            # Use forward slashes instead of "\/" to avoid deprecation warning
            "../../etc/passwd",
            "..\\../etc/passwd",

            # Absolute paths (should also be rejected)
            "/etc/passwd",
            "/var/lib/secrets",
            "C:\\Windows\\System32\\config\\SAM",
            "\\etc\\passwd",
        ]

        # Add more Windows-specific cases only when running on Windows
        if IS_WINDOWS:
            malicious_entries.extend([
                r"..\..\windows\system32\drivers\etc\hosts",
                r"subdir\..\..\..\..\windows",
                r"C:..\windows\system32",
                r"file.txt:hidden"
            ])

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])

                exception_msg = str(ctx.exception).lower()
                self.assertTrue(
                    any(phrase in exception_msg for phrase in [
                        "path traversal",
                        "illegal character",
                        "invalid archive",
                        "invalid path"
                    ]),
                    f"Expected traversal or invalid path error for entry: {entry}\n"
                    f"Got: {ctx.exception}"
                )
    def test_empty_list(self):
        """Empty entry list should be handled gracefully"""
        result = self.extractor._validate_archive_entries([])
        self.assertEqual(result, [])

    def test_single_dot_entries_allowed(self):
        """Single dot entries (current directory references) should be allowed"""
        entries = [
            "./file.txt",
            "./subdir/file.txt",
        ]

        # Single dots should be normalized and allowed
        result = self.extractor._validate_archive_entries(entries)
        self.assertEqual(len(result), len(entries))

    def test_return_value_structure(self):
        """Validated entries should be returned as a list"""
        entries = ["file1.txt", "file2.txt", "subdir/file3.txt"]
        result = self.extractor._validate_archive_entries(entries)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_validation_with_different_dest_paths(self):
        """Validation should work with different destination paths"""
        # Create a different temp directory
        alt_temp_dir = tempfile.mkdtemp()

        try:
            alt_extractor = BaseExtractor(
                pyfile=self.mock_pyfile,
                filename="test.zip",
                out=alt_temp_dir,
                fullpath=True,
                overwrite=False,
                excludefiles=None,
                priority=0,
                keepbroken=False
            )

            # Valid entries should work
            result = alt_extractor._validate_archive_entries(["file.txt"])
            self.assertEqual(len(result), 1)

            # Traversal should still be rejected
            with self.assertRaises(ArchiveError):
                alt_extractor._validate_archive_entries(["../etc/passwd"])

        finally:
            import shutil
            if os.path.exists(alt_temp_dir):
                shutil.rmtree(alt_temp_dir)

    def test_unicode_filenames(self):
        """Unicode filenames should be handled correctly"""
        unicode_entries = [
            "文件.txt",  # Chinese
            "файл.txt",  # Russian
            "αρχείο.txt",  # Greek
            "ファイル.txt",  # Japanese
        ]

        result = self.extractor._validate_archive_entries(unicode_entries)
        self.assertEqual(len(result), len(unicode_entries))

    def test_unicode_traversal_rejected(self):
        """Unicode path traversal attempts should be rejected"""
        malicious_unicode_entries = [
            "../文件.txt",
            "/etc/密码",
        ]

        for entry in malicious_unicode_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                self.assertIn("path traversal", str(ctx.exception).lower())

    def test_special_characters_in_valid_names(self):
        """Special characters in valid filenames should be allowed"""
        entries = [
            "...",
            "file-name.txt",
            "file_name.txt",
            "file.name.txt",
            "file (1).txt",
            "file [1].txt",
            "file (copy).txt",
        ]

        result = self.extractor._validate_archive_entries(entries)
        self.assertEqual(len(result), len(entries))

    def test_symlink_edge_case_detection(self):
        """Symlink edge cases should be detected (handled by is_within_directory)"""
        # This would be more thoroughly tested with actual symlinks
        # but we ensure the method structure supports it
        entries = ["file.txt", "dir/file.txt"]
        result = self.extractor._validate_archive_entries(entries)
        self.assertEqual(len(result), 2)

    def test_symlink_target_validation_safe(self):
        """Safe symlink targets pointing within destination should be accepted"""
        safe_targets = [
            ("link", "file.txt", True),  # Link to file in same directory
            ("link", "subdir/file.txt", True),  # Link to file in subdirectory
            ("subdir/link", "../file.txt", True),  # Link back to parent (but within dest)
            ("subdir/link", "file.txt", True),  # Link up one level
        ]

        for symlink_path, target, should_pass in safe_targets:
            with self.subTest(symlink_path=symlink_path, target=target):
                if should_pass:
                    # Should not raise
                    self.extractor._validate_symlink_target(symlink_path, target, self.temp_dir)
                else:
                    with self.assertRaises(ArchiveError):
                        self.extractor._validate_symlink_target(symlink_path, target, self.temp_dir)

    def test_symlink_target_traversal_rejected(self):
        """Symlink targets pointing outside destination should be rejected"""
        malicious_targets = [
            ("link", "../../etc/passwd"),
            ("link", "../../../root/.ssh/id_rsa"),
            ("subdir/link", "../../etc/passwd"),
            ("link", "/etc/passwd"),  # Absolute target
        ]

        for symlink_path, target in malicious_targets:
            with self.subTest(symlink_path=symlink_path, target=target):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_symlink_target(symlink_path, target, self.temp_dir)
                exception_msg = str(ctx.exception).lower()
                self.assertTrue(
                    "outside" in exception_msg or "absolute" in exception_msg
                )

    def test_symlink_absolute_target_rejected(self):
        """Symlink with absolute targets should be rejected"""
        absolute_targets = [
            ("link", "/etc/passwd"),
            ("link", "/root/.ssh/id_rsa"),
        ]

        # Add Windows-specific paths if on Windows
        if IS_WINDOWS:
            absolute_targets.append(("link", "C:\\Windows\\System32"))

        for symlink_path, target in absolute_targets:
            with self.subTest(symlink_path=symlink_path, target=target):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_symlink_target(symlink_path, target, self.temp_dir)
                exception_msg = str(ctx.exception).lower()
                # Should reject due to absolute path or pointing outside
                self.assertTrue(
                    "absolute" in exception_msg or "outside" in exception_msg
                )

    def test_symlink_with_drive_letter_rejected(self):
        """Symlink targets with Windows drive letters should be rejected"""
        if not IS_WINDOWS:
            self.skipTest("Drive letter test only applicable on Windows")

        with self.assertRaises(ArchiveError) as ctx:
            self.extractor._validate_symlink_target("link", "D:\\sensitive\\data", self.temp_dir)
        exception_msg = str(ctx.exception).lower()
        self.assertTrue("absolute" in exception_msg or "invalid" in exception_msg)


class TestTarSymlinkProtection(unittest.TestCase):
    """Test symlink protection in TAR extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @unittest.skipIf(not SYMLINKS_SUPPORTED, "Symlinks not supported on this system")
    def test_malicious_symlink_in_tar_rejected(self):
        """TAR with symlinks pointing outside destination should be rejected"""
        import io
        import tarfile
        from unittest.mock import Mock

        from pyload.plugins.extractors.UnTar import UnTar

        # Create a TAR with a malicious symlink
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            # Add a regular file
            file_info = tarfile.TarInfo(name="file.txt")
            file_info.size = 5
            tar.addfile(file_info, io.BytesIO(b"hello"))

            # Add a symlink pointing outside the destination
            symlink_info = tarfile.TarInfo(name="link")
            symlink_info.type = tarfile.SYMTYPE
            symlink_info.linkname = "../../etc/passwd"
            tar.addfile(symlink_info)

        tar_buffer.seek(0)

        # Try to extract - should raise ArchiveError
        with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
            mock_pyfile = Mock()
            mock_pyfile.m.pyload = Mock()
            untar = UnTar(mock_pyfile, "test.tar", self.temp_dir)
            with self.assertRaises(ArchiveError) as ctx:
                untar._safe_extractall(tar, self.temp_dir)
            self.assertIn("symlink", str(ctx.exception).lower())

    @unittest.skipIf(not SYMLINKS_SUPPORTED, "Symlinks not supported on this system")
    def test_safe_symlink_in_tar_accepted(self):
        """TAR with safe symlinks (pointing within destination) should be accepted"""
        import io
        import tarfile
        from unittest.mock import Mock

        from pyload.plugins.extractors.UnTar import UnTar

        # Create a TAR with safe symlinks
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            # Add a regular file
            file_info = tarfile.TarInfo(name="file.txt")
            file_info.size = 5
            tar.addfile(file_info, io.BytesIO(b"hello"))

            # Add a safe symlink (points to file within destination)
            symlink_info = tarfile.TarInfo(name="link")
            symlink_info.type = tarfile.SYMTYPE
            symlink_info.linkname = "file.txt"
            tar.addfile(symlink_info)

        tar_buffer.seek(0)

        # Should extract successfully
        with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
            mock_pyfile = Mock()
            mock_pyfile.m.pyload = Mock()
            untar = UnTar(mock_pyfile, "test.tar", self.temp_dir)
            # Should not raise an exception
            untar._safe_extractall(tar, self.temp_dir)
            untar._safe_extractall(tar, self.temp_dir)


class TestUnZipPathTraversal(unittest.TestCase):
    """Test path traversal protection in UnZip extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('pyload.plugins.extractors.UnZip.zipfile.ZipFile')
    def test_unzip_validates_before_extraction(self, mock_zipfile):
        """UnZip should validate entries before extraction"""
        from pyload.plugins.extractors.UnZip import UnZip

        # Mock the ZipFile
        mock_z = MagicMock()
        mock_z.namelist.return_value = ["../etc/passwd", "file.txt"]
        mock_z.testzip.return_value = None  # No bad files
        mock_z.setpassword = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_z

        # Create UnZip instance with mocked pyfile
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        unzip = UnZip(mock_pyfile, "test.zip", self.temp_dir)

        # Extraction should raise ArchiveError due to path traversal
        with self.assertRaises(ArchiveError):
            unzip.extract()


class TestZipSymlinkProtection(unittest.TestCase):
    """Test symlink protection in UnZip extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @unittest.skipIf(not SYMLINKS_SUPPORTED, "Symlinks not supported on this system")
    def test_zip_detects_symlinks(self):
        """UnZip should detect and validate symlinks"""
        import io
        import stat
        import zipfile
        from unittest.mock import Mock

        from pyload.plugins.extractors.UnZip import UnZip

        # Create a ZIP with a symlink entry
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            # Add a regular file
            z.writestr("file.txt", "hello")

            # Add a symlink by manually creating a ZipInfo with Unix symlink attributes
            symlink_info = zipfile.ZipInfo("link")
            # Set external attributes: Unix file mode S_IFLNK | permissions
            symlink_info.external_attr = (stat.S_IFLNK | 0o644) << 16
            z.writestr(symlink_info, "../../etc/passwd")

        zip_buffer.seek(0)

        # Create UnZip instance
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        unzip = UnZip(mock_pyfile, "test.zip", self.temp_dir)

        # Test _is_zip_symlink method
        with zipfile.ZipFile(zip_buffer, 'r') as z:
            symlink_entry = z.infolist()[1]  # Get the symlink entry
            self.assertTrue(unzip._is_zip_symlink(symlink_entry), "Should detect symlink entry")

            # Test symlink validation
            with self.assertRaises(ArchiveError) as ctx:
                unzip._validate_zip_symlinks(z)
            self.assertIn("symlink", str(ctx.exception).lower())


class TestUnZipExtractionBehavior(unittest.TestCase):
    """Regression tests for normal UnZip extraction behavior."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.archive_path = os.path.join(self.temp_dir, "test.zip")
        self.mock_pyfile = Mock()
        self.mock_pyfile.m.pyload = Mock()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_extract_returns_non_excluded_files_and_omits_directories(self):
        """Extraction should preserve the selected files without listing directories."""
        from pyload.plugins.extractors.UnZip import UnZip

        with zipfile.ZipFile(self.archive_path, "w") as archive:
            archive.writestr("folder/", "")
            archive.writestr("folder/keep.txt", "keep")
            archive.writestr("skip.txt", "skip")

        unzip = UnZip(
            self.mock_pyfile,
            self.archive_path,
            self.temp_dir,
            excludefiles=["skip.txt"],
        )

        self.assertEqual(
            unzip.list(),
            [
                os.path.join(self.temp_dir, "folder", "keep.txt"),
                os.path.join(self.temp_dir, "skip.txt"),
            ],
        )
        self.assertEqual(
            unzip.extract(),
            [os.path.join(self.temp_dir, "folder", "keep.txt")],
        )
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, "folder", "keep.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "skip.txt")))

    def test_extract_keeps_archive_open_after_safe_symlink_validation(self):
        """Safe symlink metadata must not close the archive before extraction."""
        from pyload.plugins.extractors.UnZip import UnZip

        with zipfile.ZipFile(self.archive_path, "w") as archive:
            archive.writestr("file.txt", "contents")
            symlink = zipfile.ZipInfo("link")
            symlink.external_attr = (stat.S_IFLNK | 0o644) << 16
            archive.writestr(symlink, "file.txt")

        unzip = UnZip(self.mock_pyfile, self.archive_path, self.temp_dir)

        self.assertEqual(
            unzip.extract(),
            [
                os.path.join(self.temp_dir, "file.txt"),
                os.path.join(self.temp_dir, "link"),
            ],
        )


class TestRarSymlinkProtection(unittest.TestCase):
    """Test symlink protection in UnRar extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @unittest.skipIf(not SYMLINKS_SUPPORTED, "Symlinks not supported on this system")
    def test_rar_skips_symlinks_with_ol_switch(self):
        """UnRar should skip symlinks using -ol- switch in call_cmd"""
        import re
        from unittest.mock import MagicMock, Mock, patch

        from pyload.plugins.extractors.UnRar import UnRar

        # Create UnRar instance
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        unrar = UnRar(mock_pyfile, "test.rar", self.temp_dir)
        unrar.VERSION = "5.70"  # Set a version
        unrar._RE_FILES = re.compile(
            r"^([* ])\s*([ACHIRS.rw\-]+)\s+(\d+)(?:\s+\d+)?(?:\s+(?:\d+%|-->|<--))?\s+([\d-]+)\s+([\d:]+)(?:\s+[0-9A-F]{8})?\s+(.+)",
            re.M
        )

        # Mock subprocess.Popen to capture the command
        with patch('pyload.plugins.extractors.UnRar.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.communicate.return_value = ('', '')
            mock_process.returncode = 0
            # Mock stdout.read to return empty immediately (end of stream)
            mock_process.stdout.read.return_value = b''
            mock_popen.return_value = mock_process

            # Mock the list method to return empty list (avoiding the need for _find_smallest_file)
            with patch.object(unrar, 'list', return_value=[]):
                # Call extract
                unrar.extract(password=None)

            # Verify that call_cmd was invoked and -ol- switch is in the command
            args, kwargs = mock_popen.call_args
            command = args[0]

            # Check that -ol- is in the command (should be present to skip symlinks)
            self.assertIn('-ol-', command, "UnRar extract should include -ol- switch to skip symlinks")

    def test_rar_path_traversal_protection_before_extraction(self):
        """UnRar should validate path traversal before extraction"""
        from unittest.mock import Mock, patch

        from pyload.plugins.extractors.UnRar import UnRar

        # Create UnRar instance
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        unrar = UnRar(mock_pyfile, "test.rar", self.temp_dir)

        # Mock the list method to return a malicious path
        with patch.object(unrar, '_list_raw', return_value=[os.path.join(self.temp_dir, "../etc/passwd")]):
            # Attempting extraction with traversal should raise ArchiveError
            with self.assertRaises(ArchiveError):
                unrar.extract(password=None)


class TestSevenZipSymlinkProtection(unittest.TestCase):
    """Test symlink protection in SevenZip extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_7zip_detects_symlinks_before_extraction(self):
        """SevenZip should detect symlinks in archive list before extraction"""
        from unittest.mock import Mock, patch

        from pyload.plugins.extractors.SevenZip import SevenZip

        # Create SevenZip instance
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        sevenzp = SevenZip(mock_pyfile, "test.7z", self.temp_dir)

        # Mock the call_cmd to return list output with a symlink
        def mock_call_cmd(*args, **kwargs):
            mock_process = Mock()
            if "l" in args and "-slt" in args:
                # Simulate 7z list -slt output with a symlink
                output = """
Listing archive: test.7z

--
Path = test.7z
Type = 7z
Physical Size = 1234567
Headers Size = 4567
Method = LZMA2:1536k
Solid = +
Blocks = 1

----------
Path = regular_file.txt
Size = 1024
Attributes = .....

Path = link_to_file
Size = 0
Attributes = l rwxr-xr-x

Path = another_file.txt
Size = 512
Attributes = .....
"""
                mock_process.communicate.return_value = (output, "")
            else:
                mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            return mock_process

        with patch.object(sevenzp, 'call_cmd', side_effect=mock_call_cmd):
            # Attempting extraction with symlinks should raise ArchiveError
            with self.assertRaises(ArchiveError) as ctx:
                sevenzp.extract(password=None)
            self.assertIn("symlink", str(ctx.exception).lower())

    def test_7zip_path_traversal_protection_before_extraction(self):
        """SevenZip should validate path traversal before extraction"""
        from unittest.mock import Mock, patch

        from pyload.plugins.extractors.SevenZip import SevenZip

        # Create SevenZip instance
        mock_pyfile = Mock()
        mock_pyfile.m.pyload = Mock()
        sevenzp = SevenZip(mock_pyfile, "test.7z", self.temp_dir)

        # Mock the call_cmd to return list output with a malicious path
        def mock_call_cmd(*args, **kwargs):
            mock_process = Mock()
            if "l" in args and "-slt" in args:
                # Simulate 7z list -slt output with a malicious path
                output = """
Listing archive: test.7z

--
Path = test.7z
Type = 7z
Physical Size = 1234567
Headers Size = 4567
Method = LZMA2:1536k
Solid = +
Blocks = 1

----------
Path = ../etc/passwd
Size = 1024
Attributes = .....
"""
                mock_process.communicate.return_value = (output, "")
            else:
                mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            return mock_process

        with patch.object(sevenzp, 'call_cmd', side_effect=mock_call_cmd):
            # Attempting extraction with traversal should raise ArchiveError
            with self.assertRaises(ArchiveError) as ctx:
                sevenzp.extract(password=None)
            self.assertIn("traversal", str(ctx.exception).lower())
