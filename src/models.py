"""Pydantic models for the ad pipeline."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class Template(BaseModel):
    """Template model for PSD templates."""
    file_id: str = Field(..., description="Unique identifier for the template")
    filename: str = Field(..., description="Filename of the PSD template")


class Product(BaseModel):
    """Product model for campaign products."""
    name: str = Field(..., description="Product name")
    file_id: str = Field(..., description="Unique identifier for the product")
    image: Optional[str] = Field(default=None, description="Product image filename")
    prompt: Optional[str] = Field(default=None, description="Prompt for generating product image")


class CampaignBrief(BaseModel):
    """Campaign brief model."""
    campaign_name: str = Field(..., description="Friendly name for the campaign")
    templates: List[Template] = Field(..., description="List of PSD templates to use")
    products: List[Product] = Field(..., description="List of products in the campaign")
    target_audience: str = Field(..., description="Target audience description")
    target_market: str = Field(..., description="Target market description")
    campaign_message: str = Field(..., description="Campaign message to be tailored by LLM")
    
    def validate_templates_exist(self, input_dir: Path) -> List[str]:
        """Validate that all template files exist in the input directory."""
        missing_templates = []
        for template in self.templates:
            template_path = input_dir / template.filename
            if not template_path.exists():
                missing_templates.append(template.filename)
        return missing_templates
    
    def validate_products(self, input_dir: Path) -> List[str]:
        """Validate that all product images exist in the input directory."""
        missing_products = []
        for product in self.products:
            if product.image:
                product_path = input_dir / product.image
                if not product_path.exists():
                    missing_products.append(product.image)
        return missing_products

