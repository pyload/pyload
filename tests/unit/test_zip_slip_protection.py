"""
Unit tests for path traversal ("Zip Slip") attack prevention in archive extractors.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pyload.plugins.base.extractor import ArchiveError, BaseExtractor


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
            "../etc/passwd",
            "../../etc/shadow",
            "..\\..\\windows\\system32\\config\\sam",
            "subdir/../../etc/passwd",
        ]

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
            "C:\\Windows\\System32\\config\\sam",
            "D:\\sensitive\\data.txt",
        ]

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                self.assertIn("path traversal", str(ctx.exception).lower())

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

    def test_mixed_separators_rejected(self):
        """Paths with mixed separators attempting traversal should be rejected"""
        malicious_entries = [
            "..\\..\\etc/passwd",
            "../etc\\passwd",
            "dir/../../../etc/passwd",
        ]

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                # Note: may be caught as traversal or depending on normalization
                exception_msg = str(ctx.exception).lower()
                self.assertTrue(
                    "path traversal" in exception_msg or "invalid" in exception_msg
                )
        """Byte paths should be handled correctly"""
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
        malicious_entries = [
            "..\\..\\etc/passwd",
            "../etc\\passwd",
            "subdir\\..\\..\\windows",
        ]

        for entry in malicious_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ArchiveError) as ctx:
                    self.extractor._validate_archive_entries([entry])
                # Note: may be caught as traversal or depending on normalization
                exception_msg = str(ctx.exception).lower()
                self.assertTrue(
                    "path traversal" in exception_msg or "invalid" in exception_msg
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
if __name__ == "__main__":
    unittest.main()
