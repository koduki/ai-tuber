"""Storage abstraction layer for filesystem and GCS."""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class StorageClient(ABC):
    """Abstract interface for storage operations."""

    @abstractmethod
    def download_file(self, bucket: str, key: str, dest: str) -> None:
        """Download a file from storage to local destination."""
        pass

    @abstractmethod
    def upload_file(self, bucket: str, key: str, src: str) -> None:
        """Upload a file from local source to storage."""
        pass

    @abstractmethod
    def read_text(self, key: str, bucket: Optional[str] = None) -> str:
        """Read text content from storage."""
        pass

    @abstractmethod
    def list_objects(self, prefix: str, bucket: Optional[str] = None) -> List[str]:
        """List objects in storage with given prefix."""
        pass


class FileSystemStorageClient(StorageClient):
    """Storage client that reads from local filesystem."""

    def __init__(self, base_path: Optional[str] = None):
        """
        FileSystem ストレージクライアントを初期化。
        
        Args:
            base_path: 基底ディレクトリ。None の場合は /app/data またはプロジェクトルート/data。
        """
        if base_path is None:
            # プロジェクトルートの data ディレクトリをデフォルトとする
            self.base_path = Path(__file__).resolve().parent.parent.parent / "data"
        else:
            self.base_path = Path(base_path)
        
        # 開発環境（dataディレクトリがない場合）への対応
        if not self.base_path.exists() and "site-packages" not in str(self.base_path):
            old_base = self.base_path
            self.base_path = Path(__file__).resolve().parent.parent.parent
            logger.warning(f"Data root {old_base} not found, falling back to project root: {self.base_path}")

        logger.info(f"FileSystemStorageClient initialized with base_path: {self.base_path}")

    def _resolve_path(self, bucket: str, key: str) -> Path:
        """Resolve bucket and key to filesystem path."""
        # In filesystem mode, bucket is treated as a subdirectory
        return self.base_path / bucket / key

    def download_file(self, bucket: str, key: str, dest: str) -> None:
        """Copy file from filesystem to destination."""
        src_path = self._resolve_path(bucket, key)
        if not src_path.exists():
            raise FileNotFoundError(f"File not found: {src_path}")
        
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(src_path, dest_path)
        logger.debug(f"Downloaded {src_path} to {dest_path}")

    def upload_file(self, bucket: str, key: str, src: str) -> None:
        """Copy file from source to filesystem storage."""
        dest_path = self._resolve_path(bucket, key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(src, dest_path)
        logger.debug(f"Uploaded {src} to {dest_path}")

    def read_text(self, key: str, bucket: Optional[str] = None) -> str:
        """Read text content from filesystem."""
        file_path = self._resolve_path(bucket or "", key)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_objects(self, prefix: str, bucket: Optional[str] = None) -> List[str]:
        """List files in filesystem with given prefix."""
        base_path = self.base_path / (bucket or "")
        if not base_path.exists():
            return []
        
        prefix_path = base_path / prefix
        results = []
        
        if prefix_path.is_dir():
            for item in prefix_path.rglob("*"):
                if item.is_file():
                    relative = item.relative_to(base_path)
                    results.append(str(relative))
        
        return results


class GcsStorageClient(StorageClient):
    """Storage client for Google Cloud Storage."""

    def __init__(self, project_id: Optional[str] = None, default_bucket: Optional[str] = None):
        """
        Initialize GCS storage client.
        
        Args:
            project_id: GCP project ID. If None, uses default credentials.
            default_bucket: Default bucket name to use if not specified in calls.
        """
        self.default_bucket = default_bucket or os.getenv("GCS_BUCKET_NAME")
        try:
            from google.cloud import storage
            self.client = storage.Client(project=project_id)
            logger.info(f"GcsStorageClient initialized with project: {project_id}, default_bucket: {self.default_bucket}")
        except ImportError:
            raise ImportError("google-cloud-storage is required for GcsStorageClient")

    def _get_bucket(self, bucket: Optional[str]):
        bucket_name = bucket or self.default_bucket
        if not bucket_name:
            raise ValueError("Bucket name must be provided or configured via GCS_BUCKET_NAME")
        return self.client.bucket(bucket_name)

    def download_file(self, bucket: str, key: str, dest: str) -> None:
        """Download file from GCS to local destination."""
        bucket_obj = self._get_bucket(bucket)
        blob = bucket_obj.blob(key)
        
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        blob.download_to_filename(dest)
        logger.debug(f"Downloaded gs://{bucket_obj.name}/{key} to {dest}")

    def upload_file(self, bucket: str, key: str, src: str) -> None:
        """Upload file from local source to GCS."""
        bucket_obj = self._get_bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.upload_from_filename(src)
        logger.debug(f"Uploaded {src} to gs://{bucket_obj.name}/{key}")

    def read_text(self, key: str, bucket: Optional[str] = None) -> str:
        """Read text content from GCS."""
        bucket_obj = self._get_bucket(bucket)
        blob = bucket_obj.blob(key)
        return blob.download_as_text()

    def list_objects(self, prefix: str, bucket: Optional[str] = None) -> List[str]:
        """List objects in GCS bucket with given prefix."""
        bucket_obj = self._get_bucket(bucket)
        blobs = bucket_obj.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]


def create_storage_client(storage_type: Optional[str] = None) -> StorageClient:
    """
    Factory function to create appropriate StorageClient.
    
    Args:
        storage_type: Type of storage ('filesystem' or 'gcs'). 
                     If None, reads from STORAGE_TYPE env var.
    
    Returns:
        StorageClient instance
    """
    if storage_type is None:
        storage_type = os.getenv("STORAGE_TYPE", "filesystem")
    
    storage_type = storage_type.lower()
    
    if storage_type == "filesystem":
        base_path = os.getenv("STORAGE_BASE_PATH")
        return FileSystemStorageClient(base_path=base_path)
    elif storage_type == "gcs":
        project_id = os.getenv("GCP_PROJECT_ID")
        return GcsStorageClient(project_id=project_id)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
