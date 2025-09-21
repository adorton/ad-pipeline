"""Configuration settings for the ad pipeline."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # API Credentials
    ffs_client_id: str = Field(..., description="Client ID for Firefly and Photoshop APIs")
    ffs_secret: str = Field(..., description="Secret for Firefly and Photoshop APIs")
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider (currently only 'openai' supported)")
    llm_api_key: str = Field(..., description="API key for LLM")
    llm_model: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    llm_base_url: Optional[str] = Field(default=None, description="Base URL for LLM (optional)")
    llm_max_tokens: int = Field(default=1000, description="Max tokens for LLM API calls")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    
    # Application Configuration
    input_directory: Path = Field(default=Path("./input"), description="Input directory for campaign files")
    output_directory: Path = Field(default=Path("./output"), description="Output directory for final renditions")
    file_encoding: str = Field(default="utf-8", description="File encoding for YAML files")
    
    # Azure Storage Configuration
    azure_storage_connection_string: Optional[str] = Field(
        default=None, 
        description="Azure Storage connection string"
    )
    azure_storage_container: str = Field(
        default="ad-pipeline-assets", 
        description="Azure Storage container name"
    )
    
    @validator('input_directory', 'output_directory')
    def validate_directories(cls, v):
        """Ensure directories are Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator('llm_provider')
    def validate_llm_provider(cls, v):
        """Validate LLM provider is supported."""
        if v != "openai":
            raise ValueError("Currently only 'openai' is supported as LLM provider")
        return v
    
    @validator('llm_temperature')
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    @validator('llm_max_tokens')
    def validate_max_tokens(cls, v):
        """Validate max tokens is positive."""
        if v <= 0:
            raise ValueError("Max tokens must be positive")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Map environment variable names to field names
        fields = {
            'ffs_client_id': 'FFS_CLIENT_ID',
            'ffs_secret': 'FFS_SECRET',
            'llm_provider': 'LLM_PROVIDER',
            'llm_api_key': 'LLM_API_KEY',
            'llm_model': 'LLM_MODEL',
            'llm_base_url': 'LLM_BASE_URL',
            'llm_max_tokens': 'LLM_MAX_TOKENS',
            'llm_temperature': 'LLM_TEMPERATURE',
            'input_directory': 'INPUT_DIRECTORY',
            'output_directory': 'OUTPUT_DIRECTORY',
            'file_encoding': 'FILE_ENCODING',
            'azure_storage_connection_string': 'AZURE_STORAGE_CONNECTION_STRING',
            'azure_storage_container': 'AZURE_STORAGE_CONTAINER',
        }
    
    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables."""
        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        
        return cls(
            ffs_client_id=os.getenv("FFS_CLIENT_ID", ""),
            ffs_secret=os.getenv("FFS_SECRET", ""),
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            input_directory=Path(os.getenv("INPUT_DIRECTORY", "./input")),
            output_directory=Path(os.getenv("OUTPUT_DIRECTORY", "./output")),
            file_encoding=os.getenv("FILE_ENCODING", "utf-8"),
            azure_storage_connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
            azure_storage_container=os.getenv("AZURE_STORAGE_CONTAINER", "ad-pipeline-assets"),
        )
    
    def ensure_directories(self) -> None:
        """Ensure input and output directories exist."""
        self.input_directory.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)
