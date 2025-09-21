"""Azure Blob Storage client for file operations."""

import logging
from pathlib import Path
from typing import Optional

from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)


class AzureBlobClient:
    """Client for Azure Blob Storage operations."""
    
    def __init__(self, account_name: str, account_key: str, container_name: str):
        """Initialize the Azure Blob client."""
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        
        # Create connection string
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={account_key};"
            f"EndpointSuffix=core.windows.net"
        )
        
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        
        # Ensure container exists
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't."""
        try:
            self.container_client.get_container_properties()
            logger.info(f"Container '{self.container_name}' exists")
        except AzureError:
            try:
                self.container_client.create_container()
                logger.info(f"Created container '{self.container_name}'")
            except AzureError as e:
                logger.error(f"Failed to create container '{self.container_name}': {e}")
                raise
    
    def upload_file(self, local_file_path: Path, blob_name: str) -> str:
        """Upload a file to Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Uploaded {local_file_path} to {blob_url}")
            return blob_url
            
        except AzureError as e:
            logger.error(f"Failed to upload {local_file_path} to {blob_name}: {e}")
            raise
    
    def download_file(self, blob_name: str, local_file_path: Path) -> None:
        """Download a file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Ensure parent directory exists
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logger.info(f"Downloaded {blob_name} to {local_file_path}")
            
        except AzureError as e:
            logger.error(f"Failed to download {blob_name} to {local_file_path}: {e}")
            raise
    
    def delete_file(self, blob_name: str) -> None:
        """Delete a file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted {blob_name} from Azure Blob Storage")
            
        except AzureError as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            raise
    
    def get_blob_url(self, blob_name: str) -> str:
        """Get the URL for a blob."""
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.url

