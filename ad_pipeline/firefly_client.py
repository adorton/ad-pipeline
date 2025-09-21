"""Firefly Services client for image generation."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class FireflyClient:
    """Client for Adobe Firefly Services API."""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize the Firefly client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://firefly-api.adobe.io/v2"
        self.access_token = None
        
        # Get access token
        self._get_access_token()
    
    def _get_access_token(self):
        """Get access token for Firefly API."""
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
            
        except requests.RequestException as e:
            logger.error(f"Failed to get Firefly access token: {e}")
            raise
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024) -> bytes:
        """Generate an image using Firefly API."""
        if not self.access_token:
            raise ValueError("No access token available")
        
        url = f"{self.base_url}/images/generate"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-API-Key": self.client_id
        }
        
        payload = {
            "prompt": prompt,
            "size": {
                "width": width,
                "height": height
            },
            "n": 1
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract image URL from response
            if "outputs" in result and len(result["outputs"]) > 0:
                image_url = result["outputs"][0]["image"]["url"]
                
                # Download the image
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                
                logger.info(f"Generated image for prompt: {prompt[:50]}...")
                return image_response.content
            else:
                raise ValueError("No image generated in response")
                
        except requests.RequestException as e:
            logger.error(f"Failed to generate image: {e}")
            raise

