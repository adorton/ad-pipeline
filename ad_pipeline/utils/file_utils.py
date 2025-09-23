"""File utility functions."""

import os
from pathlib import Path
from typing import List


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()


def find_yaml_files(directory: Path) -> List[Path]:
    """Find all YAML files in the given directory."""
    if not directory.exists():
        return []
    
    yaml_files = []
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.yml', '.yaml']:
            yaml_files.append(file_path)
    
    return sorted(yaml_files)


def get_safe_filename(filename: str) -> str:
    """Convert filename to a safe format for file systems."""
    # Remove or replace characters that might cause issues
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_filename = "".join(c if c in safe_chars else "_" for c in filename)
    
    # Remove multiple consecutive underscores
    while "__" in safe_filename:
        safe_filename = safe_filename.replace("__", "_")
    
    # Remove leading/trailing underscores
    safe_filename = safe_filename.strip("_")
    
    return safe_filename


def get_rendition_filename(product_file_id: str, template_file_id: str) -> str:
    """Generate rendition filename following the naming convention."""
    return f"{product_file_id}_{template_file_id}.png"
