"""Configuration management for the ad pipeline."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration model for the ad pipeline."""
    
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
    file_encoding: str = Field(default="utf-8", description="File encoding for campaign YAML files")
    
    # Azure Storage Configuration
    azure_storage_account_name: str = Field(..., description="Azure storage account name")
    azure_storage_account_key: str = Field(..., description="Azure storage account key")
    azure_container_name: str = Field(default="ad-pipeline", description="Azure container name")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
    
    # Map environment variable names to config fields
    env_mapping = {
        "FFS_CLIENT_ID": "ffs_client_id",
        "FFS_SECRET": "ffs_secret",
        "LLM_PROVIDER": "llm_provider",
        "LLM_API_KEY": "llm_api_key",
        "LLM_MODEL": "llm_model",
        "LLM_BASE_URL": "llm_base_url",
        "LLM_MAX_TOKENS": "llm_max_tokens",
        "LLM_TEMPERATURE": "llm_temperature",
        "INPUT_DIRECTORY": "input_directory",
        "OUTPUT_DIRECTORY": "output_directory",
        "FILE_ENCODING": "file_encoding",
        "AZURE_STORAGE_ACCOUNT_NAME": "azure_storage_account_name",
        "AZURE_STORAGE_ACCOUNT_KEY": "azure_storage_account_key",
        "AZURE_CONTAINER_NAME": "azure_container_name",
    }
    
    # Create config dict from environment variables
    config_dict = {}
    for env_var, field_name in env_mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if field_name in ["llm_max_tokens"]:
                config_dict[field_name] = int(value)
            elif field_name in ["llm_temperature"]:
                config_dict[field_name] = float(value)
            elif field_name in ["input_directory", "output_directory"]:
                config_dict[field_name] = Path(value)
            elif field_name == "llm_base_url" and value == "":
                config_dict[field_name] = None
            else:
                config_dict[field_name] = value
    
    return Config(**config_dict)

