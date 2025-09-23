"""Photoshop API client for text replacement, image processing, and rendition creation."""

import base64
import io
import time
from typing import Optional

import requests

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
            response_data = response.json()
            status_url = response_data['_links']['self']['href']
            # loop to get result
            tries = 0
            while tries < 5:
                status_res = requests.get(status_url, headers=headers)
                status_res.raise_for_status()
                status_data = status_res.json()
                output = status_data['outputs'][0]
                if output['status'] not in ('failed', 'succeeded'):
                    logger.info(f'Photoshop API is working on {endpoint} endpoint, waiting 5 seconds')
                    time.sleep(5)
                elif output['status'] == 'failed':
                    raise Exception(f"Call to '{endpoint}' failed: {output['errors']}")
                elif output['status'] == 'succeeded':
                    return output['_links']['renditions'][0]['href']
                tries += 1
            raise Exception("Photoshop API request timed out")

        except Exception as e:
            logger.error(f"Photoshop API request failed: {e}")
            raise
    
    def replace_text(
        self,
        input_psd_url: bytes,
        output_psd_url: bytes,
        layers: list[tuple[str, str]],
    ) -> bytes:
        """Replace text in a PSD file.
        
        Args:
            input_psd_url: Presigned URL for input PSD file
            output_psd_url: Presigned URL for output PSD file
            layers: list of tuples each taking the form (text_layer_name, text_content)
        
        Returns:
            Presigned URL of output PSD
        
        Raises:
            Exception: If text replacement fails
        """

        layer_data = list()
        for text_layer_name, text_content in layers:
            layer_data.append({
                "name": text_layer_name,
                "text": {
                    "content": text_content,
                }
            })

        data = {
            "inputs": [
                {
                    "href": input_psd_url,
                    "storage": "azure"
                }
            ],
            "options": {
                "layers": layer_data,
            },
            "outputs": [{
                "href": output_psd_url,
                "storage": "azure",
                "type": "vnd.adobe.photoshop",
                "overwrite": True
            }]
        }

        try:
            result = self._make_request("text", data)

        except Exception as e:
            logger.error(f"Failed to replace text in PSD: {e}")
            raise
        return result
    
    def crop_product_image(
        self,
        input_url: str,
        output_url: str
    ) -> str:
        """Crop a product image to specified dimensions.
        
        Args:
            input_url: Presigned URL for input image
            output_url: Presigned URL for output image

        Returns:
            Presigned URL of cropped image
        
        Raises:
            Exception: If cropping fails
        """
        data = {
            "inputs": [
                {
                    "href": input_url,
                    "storage": "azure"
                }
            ],
            "options": {
                "unit": "Pixels",
                "width": 20,
                "height": 20,
            },
            "outputs": [{
                "href": output_url,
                "storage": "azure",
                "type": "image/jpeg",
                "overwrite": True,
                "quality": 12
            }]
        }

        try:
            result = self._make_request("productCrop", data)

        except Exception as e:
            logger.error(f"Failed to crop image: {e}")
            raise
        return result

    def remove_background(self, input_url: str) -> Optional[str]:
        """Remove background from an image using Photoshop API.
        
        Args:
            input_url: Input image URL
        
        Returns:
            Presigned URL of processed image (None if there was a problem)
        
        Raises:
            Exception: If background removal fails
        """
        # this uses a different base URL from the other endpoints
        url = "https://image.adobe.io/v2/remove-background"
        data = {
            "image": {
                "source": {
                    "url": input_url,
                }
            },
            "mode": "cutout",
            "output": {
                "mediaType": "image/png"
            },
            "trim": True,
            "backgroundColor": {
                "red": 255,
                "green": 255,
                "blue": 255,
                "alpha": 0
            },
            "colorDecontamination": 1
        }

        access_token = self._get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-API-Key": self.client_id,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            response_data = response.json()
            status_url = response_data['statusUrl']
            # loop to get result
            tries = 0
            while tries < 5:
                status_res = requests.get(status_url, headers=headers)
                status_res.raise_for_status()
                status_data = status_res.json()

                if status_data['status'] not in ('failed', 'succeeded'):
                    logger.info(f'Photoshop API is working on remove background endpoint, waiting 5 seconds')
                    time.sleep(5)
                elif status_data['status'] == 'failed':
                    breakpoint()
                    raise Exception(f"Call to 'remove background' failed: {status_data['message']}")
                elif status_data['status'] == 'succeeded':
                    return status_data['result']['outputs'][0]['destination']['url']
                tries += 1
            raise Exception("Photoshop API request timed out")

        except Exception as e:
            logger.error(f"Failed to remove background: {e}")
            raise
        return None

    def replace_smart_object(
        self,
        input_psd_url: str,
        smart_object_name: str,
        replace_image_url: str,
        output_psd_url: str,
    ) -> str:
        """Replace a smart object in a PSD file.
        
        Args:
            psd_url: URL to PSD file
            smart_object_name: Name of the smart object to replace
            replace_image_url: URL to replacement image
            output_psd_url: Presigned URL of final PSD
        
        Returns:
            Presigned URL of final PSD
        
        Raises:
            Exception: If smart object replacement fails
        """
        data = {
            "inputs": [{
                "href": input_psd_url,
                "storage": "azure"
            }],
            "outputs": [{
                "href": output_psd_url,
                "storage": "azure",
                "type": "image/vnd.adobe.photoshop",
            }],
            "options": {
                "layers": [{
                    "name": smart_object_name,
                    "input": {
                        "href": replace_image_url,
                        "storage": "azure"
                    },
                }]
            }
        }

        try:
            result = self._make_request("smartObject", data)

        except Exception as e:
            logger.error(f"Failed to replace smart object: {e}")
            raise
        return result

    def create_rendition(
        self,
        psd_url: str,
        rendition_url: str,
        file_format: str = "image/png"
    ) -> str:
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

        data = {
            "inputs": [{
                "href": psd_url,
                "storage": "azure"

            }],
            "outputs": [{
                "href": rendition_url,
                "storage": "azure",
                "type": file_format,
            }]
        }


        try:
            result = self._make_request("renditionCreate", data)

        except Exception as e:
            logger.error(f"Failed to create rendition: {e}")
            raise
        return result
