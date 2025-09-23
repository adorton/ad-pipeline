"""Azure Blob Storage client for file uploads and downloads."""

import io
import datetime
from pathlib import Path
from typing import Optional

from azure.storage.blob import BlobServiceClient, generate_container_sas, ContainerSasPermissions, ContentSettings
from azure.core.exceptions import AzureError

from ..utils.logging_utils import get_logger


logger = get_logger(__name__)


class AzureBlobClient:
    """Azure Blob Storage client for managing campaign assets."""
    
    def __init__(self, account_key: str, account_name: str, container_name: str):
        """Initialize Azure Blob Storage client.
        
        Args:
            account_key: Storage account key
            account_name: Storage account name
            container_name: Storage container name
        """
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={account_key};"
            f"EndpointSuffix=core.windows.net"
        )
        self.account_key = account_key
        self.account_name = account_name
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.client.get_container_client(container_name)
        
        # Ensure container exists
        self._ensure_container_exists()
        self.container_sas = self._generate_container_sas()

    def _ensure_container_exists(self) -> None:
        """Ensure the blob container exists, create if it doesn't."""
        try:
            self.container_client.create_container()
            logger.info(f"Created Azure container: {self.container_name}")
        except AzureError as e:
            if "ContainerAlreadyExists" in str(e):
                logger.debug(f"Azure container already exists: {self.container_name}")
            else:
                logger.error(f"Failed to create Azure container: {e}")
                raise
    
    def upload_file(self, local_file_path: Path, blob_name: str) -> str:
        """Upload a file to Azure Blob Storage.
        
        Args:
            local_file_path: Path to the local file
            blob_name: Name for the blob in storage
        
        Returns:
            URL of the uploaded blob
        
        Raises:
            FileNotFoundError: If local file doesn't exist
            AzureError: If upload fails
        """
        if not local_file_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        
        try:
            content_type = 'application/octet-stream'
            if local_file_path.suffix in ('.jpg', '.jpeg'):
                content_type = 'image/jpeg'
            elif local_file_path.suffix == '.png':
                content_type = 'image/png'

            content_settings = ContentSettings(content_type=content_type)

            with open(local_file_path, "rb") as data:
                blob_client = self.container_client.get_blob_client(blob_name)
                blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
                
            blob_url = blob_client.url
            logger.info(f"Uploaded file to Azure: {blob_name}")
            return blob_url
            
        except AzureError as e:
            logger.error(f"Failed to upload file to Azure: {e}")
            raise
    
    def upload_data(self, data: bytes, blob_name: str) -> str:
        """Upload data bytes to Azure Blob Storage.
        
        Args:
            data: Data bytes to upload
            blob_name: Name for the blob in storage
        
        Returns:
            URL of the uploaded blob
        
        Raises:
            AzureError: If upload fails
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Uploaded data to Azure: {blob_name}")
            return blob_url
            
        except AzureError as e:
            logger.error(f"Failed to upload data to Azure: {e}")
            raise
    
    def download_file(self, blob_name: str, local_file_path: Path) -> None:
        """Download a file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob in storage
            local_file_path: Local path to save the file
        
        Raises:
            AzureError: If download fails
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Ensure local directory exists
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_file_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"Downloaded file from Azure: {blob_name}")
            
        except AzureError as e:
            logger.error(f"Failed to download file from Azure: {e}")
            raise
    
    def download_data(self, blob_name: str) -> bytes:
        """Download data from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob in storage
        
        Returns:
            Downloaded data as bytes
        
        Raises:
            AzureError: If download fails
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            data = download_stream.readall()
            
            logger.info(f"Downloaded data from Azure: {blob_name}")
            return data
            
        except AzureError as e:
            logger.error(f"Failed to download data from Azure: {e}")
            raise
    
    def delete_blob(self, blob_name: str) -> None:
        """Delete a blob from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to delete
        
        Raises:
            AzureError: If deletion fails
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Deleted blob from Azure: {blob_name}")
            
        except AzureError as e:
            logger.error(f"Failed to delete blob from Azure: {e}")
            raise
    
    def list_blobs(self, prefix: str = "") -> list[str]:
        """List blobs in the container.
        
        Args:
            prefix: Optional prefix to filter blobs
        
        Returns:
            List of blob names
        
        Raises:
            AzureError: If listing fails
        """
        try:
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            blob_names = [blob.name for blob in blobs]
            
            logger.debug(f"Listed {len(blob_names)} blobs with prefix: {prefix}")
            return blob_names
            
        except AzureError as e:
            logger.error(f"Failed to list blobs from Azure: {e}")
            raise
    
    def blob_exists(self, blob_name: str) -> bool:
        """Check if a blob exists in the container.
        
        Args:
            blob_name: Name of the blob to check
        
        Returns:
            True if blob exists, False otherwise
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.get_blob_properties()
            return True
        except AzureError:
            return False

    def get_presigned_url(self, file_path: str):
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{file_path}?{self.container_sas}"

    def _generate_container_sas(self):
        # Create a SAS token that's valid for one day, as an example
        start_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = start_time + datetime.timedelta(days=1)

        sas_token = generate_container_sas(
            account_name=self.container_client.account_name,
            container_name=self.container_client.container_name,
            account_key=self.account_key,
            permission=ContainerSasPermissions(read=True, write=True),
            expiry=expiry_time,
            start=start_time
        )

        return sas_token
