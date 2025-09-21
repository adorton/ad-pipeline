"""Data models for campaign briefs and related entities."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class Template(BaseModel):
    """PSD template definition."""
    
    file_id: str = Field(..., description="Unique identifier for the template")
    filename: str = Field(..., description="Filename of the PSD template")
    
    @validator('file_id')
    def validate_file_id(cls, v):
        """Validate file_id is not empty."""
        if not v or not v.strip():
            raise ValueError("file_id cannot be empty")
        return v.strip()
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename has .psd extension."""
        if not v.lower().endswith('.psd'):
            raise ValueError("Template filename must have .psd extension")
        return v


class Product(BaseModel):
    """Product definition for campaign."""
    
    name: str = Field(..., description="Product name")
    file_id: str = Field(..., description="Unique identifier for the product")
    image: Optional[str] = Field(default=None, description="Product image filename")
    prompt: Optional[str] = Field(default=None, description="Prompt for image generation")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()
    
    @validator('file_id')
    def validate_file_id(cls, v):
        """Validate file_id is not empty."""
        if not v or not v.strip():
            raise ValueError("file_id cannot be empty")
        return v.strip()
    
    @validator('image')
    def validate_image(cls, v):
        """Validate image filename if provided."""
        if v is not None and v.strip():
            v = v.strip()
            if not v.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Image filename must have .jpg, .jpeg, or .png extension")
        return v
    
    def has_image(self) -> bool:
        """Check if product has an image file specified."""
        return self.image is not None and self.image.strip() != ""
    
    def has_prompt(self) -> bool:
        """Check if product has a prompt for image generation."""
        return self.prompt is not None and self.prompt.strip() != ""
    
    def can_generate_image(self) -> bool:
        """Check if product can generate an image (has prompt but no image)."""
        return not self.has_image() and self.has_prompt()


class Campaign(BaseModel):
    """Campaign brief definition."""
    
    campaign_name: str = Field(..., description="Friendly name for the campaign")
    templates: List[Template] = Field(..., description="List of PSD templates to use")
    products: List[Product] = Field(..., description="List of products in the campaign")
    target_audience: str = Field(..., description="Target audience description")
    target_market: str = Field(..., description="Target market description")
    campaign_message: str = Field(..., description="Base campaign message")
    
    @validator('campaign_name')
    def validate_campaign_name(cls, v):
        """Validate campaign name is not empty."""
        if not v or not v.strip():
            raise ValueError("Campaign name cannot be empty")
        return v.strip()
    
    @validator('templates')
    def validate_templates(cls, v):
        """Validate templates list is not empty."""
        if not v:
            raise ValueError("At least one template must be specified")
        return v
    
    @validator('products')
    def validate_products(cls, v):
        """Validate products list is not empty."""
        if not v:
            raise ValueError("At least one product must be specified")
        return v
    
    @validator('target_audience', 'target_market', 'campaign_message')
    def validate_text_fields(cls, v):
        """Validate text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Text field cannot be empty")
        return v.strip()
    
    def get_template_by_file_id(self, file_id: str) -> Optional[Template]:
        """Get template by file_id."""
        for template in self.templates:
            if template.file_id == file_id:
                return template
        return None
    
    def get_product_by_file_id(self, file_id: str) -> Optional[Product]:
        """Get product by file_id."""
        for product in self.products:
            if product.file_id == file_id:
                return product
        return None
    
    def validate_template_files_exist(self, input_directory: Path) -> List[str]:
        """Validate that all template files exist in the input directory.
        
        Returns:
            List of missing template filenames.
        """
        missing_files = []
        for template in self.templates:
            template_path = input_directory / template.filename
            if not template_path.exists():
                missing_files.append(template.filename)
        return missing_files
    
    def validate_product_images_exist(self, input_directory: Path) -> List[str]:
        """Validate that all product image files exist in the input directory.
        
        Returns:
            List of missing product image filenames.
        """
        missing_files = []
        for product in self.products:
            if product.has_image():
                image_path = input_directory / product.image
                if not image_path.exists():
                    missing_files.append(product.image)
        return missing_files
    
    def get_products_needing_image_generation(self) -> List[Product]:
        """Get products that need image generation (have prompt but no image)."""
        return [product for product in self.products if product.can_generate_image()]
    
    def get_products_with_images(self) -> List[Product]:
        """Get products that have image files specified."""
        return [product for product in self.products if product.has_image()]
