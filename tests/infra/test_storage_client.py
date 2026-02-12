"""Tests for StorageClient abstraction."""
import os
import tempfile
from pathlib import Path
import pytest
from infra.storage_client import (
    FileSystemStorageClient,
    create_storage_client,
)


class TestFileSystemStorageClient:
    """Test FileSystemStorageClient implementation."""

    def test_read_text(self, tmp_path):
        """Test reading text file from filesystem."""
        # Setup
        test_dir = tmp_path / "data" / "mind" / "ren"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "persona.md"
        test_content = "# Test Persona\nThis is a test."
        test_file.write_text(test_content, encoding="utf-8")
        
        # Create client with tmp_path as base
        client = FileSystemStorageClient(base_path=str(tmp_path))
        
        # Test
        result = client.read_text("data/mind/ren", "persona.md")
        assert result == test_content

    def test_download_file(self, tmp_path):
        """Test downloading (copying) file."""
        # Setup source
        src_dir = tmp_path / "src" / "data"
        src_dir.mkdir(parents=True)
        src_file = src_dir / "test.txt"
        src_file.write_text("test content", encoding="utf-8")
        
        # Setup destination
        dest_file = tmp_path / "dest" / "test.txt"
        
        # Create client
        client = FileSystemStorageClient(base_path=str(tmp_path / "src"))
        
        # Test
        client.download_file("data", "test.txt", str(dest_file))
        assert dest_file.exists()
        assert dest_file.read_text(encoding="utf-8") == "test content"

    def test_upload_file(self, tmp_path):
        """Test uploading (copying) file."""
        # Setup source
        src_file = tmp_path / "source.txt"
        src_file.write_text("upload test", encoding="utf-8")
        
        # Create client
        client = FileSystemStorageClient(base_path=str(tmp_path))
        
        # Test
        client.upload_file("uploads", "uploaded.txt", str(src_file))
        
        uploaded_file = tmp_path / "uploads" / "uploaded.txt"
        assert uploaded_file.exists()
        assert uploaded_file.read_text(encoding="utf-8") == "upload test"

    def test_file_not_found(self, tmp_path):
        """Test FileNotFoundError when file doesn't exist."""
        client = FileSystemStorageClient(base_path=str(tmp_path))
        
        with pytest.raises(FileNotFoundError):
            client.read_text("nonexistent", "file.txt")


class TestStorageClientFactory:
    """Test storage client factory function."""

    def test_create_filesystem_client(self, monkeypatch):
        """Test creating FileSystemStorageClient via factory."""
        monkeypatch.setenv("STORAGE_TYPE", "filesystem")
        
        client = create_storage_client()
        assert isinstance(client, FileSystemStorageClient)

    def test_create_filesystem_client_default(self, monkeypatch):
        """Test default is FileSystemStorageClient."""
        monkeypatch.delenv("STORAGE_TYPE", raising=False)
        
        client = create_storage_client()
        assert isinstance(client, FileSystemStorageClient)

    def test_invalid_storage_type(self):
        """Test invalid storage type raises error."""
        with pytest.raises(ValueError, match="Unknown storage type"):
            create_storage_client("invalid_type")
