"""Photoshop API client for text replacement, image processing, and rendition creation."""

import base64
import io
from typing import Optional

import requests
from PIL import Image

from ..utils.logging_utils import get_logger


logger = get_logger(__name__)


class PhotoshopClient:
    """Photoshop API client for PSD manipulation and image processing."""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize Photoshop client.
        
        Args:
            client_id: Photoshop API client ID
            client_secret: Photoshop API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://image.adobe.io/pie/psdService"
    
    def _get_access_token(self) -> str:
        """Get access token for Photoshop API.
        
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
            "scope": "openid,AdobeID,firefly_api,ff_apis,ps_api"
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            logger.info("Successfully obtained Photoshop access token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get Photoshop access token: {e}")
            raise
    
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """Make a request to the Photoshop API.
        
        Args:
            endpoint: API endpoint
            data: Request data
        
        Returns:
            API response data
        
        Raises:
            Exception: If request fails
        """
        access_token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-API-Key": self.client_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Photoshop API request failed: {e}")
            raise
    
    def replace_text(
        self,
        psd_data: bytes,
        text_layer_name: str,
        new_text: str
    ) -> bytes:
        """Replace text in a PSD file.
        
        Args:
            psd_data: PSD file data as bytes
            text_layer_name: Name of the text layer to replace
            new_text: New text content
        
        Returns:
            Modified PSD data as bytes
        
        Raises:
            Exception: If text replacement fails
        """
        psd_base64 = base64.b64encode(psd_data).decode('utf-8')
        
        data = {
            "inputs": [
                {
                    "href": f"data:application/octet-stream;base64,{psd_base64}",
                    "storage": "base64"
                }
            ],
            "options": {
                "layers": [
                    {
                        "name": text_layer_name,
                        "text": {
                            "content": new_text
                        }
                    }
                ]
            }
        }
        
        try:
            result = self._make_request("replaceText", data)
            
            # Extract the modified PSD data
            if "outputs" in result and result["outputs"]:
                output = result["outputs"][0]
                if "href" in output:
                    # Download the modified PSD
                    response = requests.get(output["href"])
                    response.raise_for_status()
                    
                    modified_psd = response.content
                    logger.info(f"Successfully replaced text in layer: {text_layer_name}")
                    return modified_psd
                else:
                    raise Exception("No output href found in Photoshop response")
            else:
                raise Exception("No outputs found in Photoshop response")
                
        except Exception as e:
            logger.error(f"Failed to replace text in PSD: {e}")
            raise
    
    def crop_product_image(
        self,
        image_data: bytes,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:
        """Crop a product image to specified dimensions.
        
        Args:
            image_data: Image data as bytes
            width: Target width in pixels
            height: Target height in pixels
        
        Returns:
            Cropped image data as bytes
        
        Raises:
            Exception: If cropping fails
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate crop box (center crop)
                img_width, img_height = img.size
                
                # Calculate aspect ratio
                target_ratio = width / height
                img_ratio = img_width / img_height
                
                if img_ratio > target_ratio:
                    # Image is wider, crop width
                    new_width = int(img_height * target_ratio)
                    left = (img_width - new_width) // 2
                    crop_box = (left, 0, left + new_width, img_height)
                else:
                    # Image is taller, crop height
                    new_height = int(img_width / target_ratio)
                    top = (img_height - new_height) // 2
                    crop_box = (0, top, img_width, top + new_height)
                
                # Crop and resize
                cropped_img = img.crop(crop_box)
                resized_img = cropped_img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save to bytes
                output = io.BytesIO()
                resized_img.save(output, format='PNG')
                cropped_data = output.getvalue()
                
                logger.info(f"Successfully cropped image to {width}x{height}")
                return cropped_data
                
        except Exception as e:
            logger.error(f"Failed to crop product image: {e}")
            raise
    
    def remove_background(self, image_data: bytes) -> bytes:
        """Remove background from an image using Photoshop API.
        
        Args:
            image_data: Image data as bytes
        
        Returns:
            Image with background removed as bytes
        
        Raises:
            Exception: If background removal fails
        """
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            "inputs": [
                {
                    "href": f"data:image/png;base64,{image_base64}",
                    "storage": "base64"
                }
            ],
            "options": {
                "removeBackground": True
            }
        }
        
        try:
            result = self._make_request("removeBackground", data)
            
            # Extract the processed image data
            if "outputs" in result and result["outputs"]:
                output = result["outputs"][0]
                if "href" in output:
                    # Download the processed image
                    response = requests.get(output["href"])
                    response.raise_for_status()
                    
                    processed_image = response.content
                    logger.info("Successfully removed background from image")
                    return processed_image
                else:
                    raise Exception("No output href found in Photoshop response")
            else:
                raise Exception("No outputs found in Photoshop response")
                
        except Exception as e:
            logger.error(f"Failed to remove background: {e}")
            raise
    
    def replace_smart_object(
        self,
        psd_data: bytes,
        smart_object_name: str,
        new_image_data: bytes
    ) -> bytes:
        """Replace a smart object in a PSD file.
        
        Args:
            psd_data: PSD file data as bytes
            smart_object_name: Name of the smart object to replace
            new_image_data: New image data as bytes
        
        Returns:
            Modified PSD data as bytes
        
        Raises:
            Exception: If smart object replacement fails
        """
        psd_base64 = base64.b64encode(psd_data).decode('utf-8')
        image_base64 = base64.b64encode(new_image_data).decode('utf-8')
        
        data = {
            "inputs": [
                {
                    "href": f"data:application/octet-stream;base64,{psd_base64}",
                    "storage": "base64"
                }
            ],
            "options": {
                "layers": [
                    {
                        "name": smart_object_name,
                        "smartObject": {
                            "href": f"data:image/png;base64,{image_base64}",
                            "storage": "base64"
                        }
                    }
                ]
            }
        }
        
        try:
            result = self._make_request("replaceSmartObject", data)
            
            # Extract the modified PSD data
            if "outputs" in result and result["outputs"]:
                output = result["outputs"][0]
                if "href" in output:
                    # Download the modified PSD
                    response = requests.get(output["href"])
                    response.raise_for_status()
                    
                    modified_psd = response.content
                    logger.info(f"Successfully replaced smart object: {smart_object_name}")
                    return modified_psd
                else:
                    raise Exception("No output href found in Photoshop response")
            else:
                raise Exception("No outputs found in Photoshop response")
                
        except Exception as e:
            logger.error(f"Failed to replace smart object: {e}")
            raise
    
    def create_rendition(
        self,
        psd_data: bytes,
        format: str = "png",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> bytes:
        """Create a rendition from a PSD file.
        
        Args:
            psd_data: PSD file data as bytes
            format: Output format (png, jpg, etc.)
            width: Optional target width
            height: Optional target height
        
        Returns:
            Rendered image data as bytes
        
        Raises:
            Exception: If rendition creation fails
        """
        psd_base64 = base64.b64encode(psd_data).decode('utf-8')
        
        options = {
            "format": format
        }
        
        if width and height:
            options["width"] = width
            options["height"] = height
        
        data = {
            "inputs": [
                {
                    "href": f"data:application/octet-stream;base64,{psd_base64}",
                    "storage": "base64"
                }
            ],
            "options": options
        }
        
        try:
            result = self._make_request("createRendition", data)
            
            # Extract the rendered image data
            if "outputs" in result and result["outputs"]:
                output = result["outputs"][0]
                if "href" in output:
                    # Download the rendered image
                    response = requests.get(output["href"])
                    response.raise_for_status()
                    
                    rendered_image = response.content
                    logger.info(f"Successfully created {format} rendition")
                    return rendered_image
                else:
                    raise Exception("No output href found in Photoshop response")
            else:
                raise Exception("No outputs found in Photoshop response")
                
        except Exception as e:
            logger.error(f"Failed to create rendition: {e}")
            raise
