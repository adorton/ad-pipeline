"""Firefly Services API client for image generation."""

import base64
import io
from typing import Optional

import requests
from PIL import Image

from ..utils.logging_utils import get_logger


logger = get_logger(__name__)


class FireflyClient:
    """Firefly Services API client for generating product images."""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize Firefly client.
        
        Args:
            client_id: Firefly Services client ID
            client_secret: Firefly Services client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://firefly-api.adobe.io/v2"
    
    def _get_access_token(self) -> str:
        """Get access token for Firefly API.
        
        Returns:
            Access token string
        
        Raises:
            Exception: If token request fails
        """
        if self.access_token:
            return self.access_token
        
        token_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid,AdobeID,firefly_api,ff_apis"
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            logger.info("Successfully obtained Firefly access token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get Firefly access token: {e}")
            raise
    
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "photographic"
    ) -> bytes:
        """Generate an image using Firefly API.
        
        Args:
            prompt: Text prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            style: Image style (photographic, artistic, etc.)
        
        Returns:
            Generated image as bytes
        
        Raises:
            Exception: If image generation fails
        """
        access_token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-API-Key": self.client_id,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "size": {
                "width": width,
                "height": height
            },
            "style": {
                "preset": style
            },
            "n": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/images/generate",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract image data from response
            if "outputs" in result and result["outputs"]:
                image_data = result["outputs"][0]
                
                # Get the image URL and download it
                if "image" in image_data and "presignedUrl" in image_data["image"]:
                    image_url = image_data["image"]["presignedUrl"]
                    
                    # Download the image
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    
                    image_bytes = image_response.content
                    
                    logger.info(f"Successfully generated image with prompt: {prompt[:50]}...")
                    return image_bytes
                else:
                    raise Exception("No image URL found in Firefly response")
            else:
                raise Exception("No outputs found in Firefly response")
                
        except Exception as e:
            logger.error(f"Failed to generate image with Firefly: {e}")
            raise
    
    def generate_product_image(
        self,
        product_name: str,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:
        """Generate a product image with optimized settings.
        
        Args:
            product_name: Name of the product
            prompt: Detailed prompt for the product image
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            Generated product image as bytes
        
        Raises:
            Exception: If image generation fails
        """
        # Enhance prompt for product photography
        enhanced_prompt = f"""
        {prompt}
        
        Professional product photography style.
        Clean white background.
        High quality, commercial photography.
        Sharp focus, good lighting.
        Suitable for e-commerce and advertising.
        """
        
        return self.generate_image(
            prompt=enhanced_prompt,
            width=width,
            height=height,
            style="photographic"
        )
    
    def validate_image(self, image_bytes: bytes) -> bool:
        """Validate that the generated image is valid.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            True if image is valid, False otherwise
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Check if image can be opened and has reasonable dimensions
                width, height = img.size
                return width > 0 and height > 0
        except Exception as e:
            logger.warning(f"Invalid image generated: {e}")
            return False
