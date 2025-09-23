"""LLM client for generating campaign messaging and CTAs."""

from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..utils.logging_utils import get_logger


logger = get_logger(__name__)


class LLMClient:
    """OpenAI client for generating campaign content."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            base_url: Optional base URL for API calls
            max_tokens: Maximum tokens for completions
            temperature: Temperature for completions
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def generate_campaign_message(
        self,
        base_message: str,
        target_audience: str,
        target_market: str,
        product_name: str
    ) -> str:
        """Generate tailored campaign message for a product.
        
        Args:
            base_message: Base campaign message
            target_audience: Target audience description
            target_market: Target market description
            product_name: Name of the product
        
        Returns:
            Generated campaign message
        
        Raises:
            Exception: If API call fails
        """
        prompt = f"""
        You are a marketing copywriter creating compelling ad copy for a product.
        
        Base campaign message: {base_message}
        Product name: {product_name}
        Target audience: {target_audience}
        Target market: {target_market}
        
        Create a tailored, compelling campaign message that:
        1. Speaks directly to the target audience
        2. Is appropriate for the target market (consider language, cultural context)
        3. Highlights the product name naturally
        4. Maintains the core message but makes it more specific and engaging
        5. Is concise but impactful (2-3 sentences max)
        
        Return only the final campaign message, no additional text.
        """
        
        try:
            response = self._make_completion_request(prompt)
            message = response.choices[0].message.content.strip()
            
            logger.info(f"Generated campaign message for product: {product_name}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate campaign message: {e}")
            raise
    
    def generate_call_to_action(
        self,
        product_name: str,
        target_audience: str,
        target_market: str,
        campaign_message: str
    ) -> str:
        """Generate call-to-action text for a product.
        
        Args:
            product_name: Name of the product
            target_audience: Target audience description
            target_market: Target market description
            campaign_message: The campaign message for context
        
        Returns:
            Generated call-to-action text
        
        Raises:
            Exception: If API call fails
        """
        prompt = f"""
        You are a marketing copywriter creating compelling call-to-action (CTA) text for a product.
        
        Product name: {product_name}
        Target audience: {target_audience}
        Target market: {target_market}
        Campaign message: {campaign_message}
        
        Create a compelling call-to-action that:
        1. Is appropriate for the target audience and market
        2. Creates urgency or excitement
        3. Is action-oriented (tells the audience what to do)
        4. Is concise (1-4 words typically)
        5. Matches the tone of the campaign message
        
        Examples of good CTAs: "Shop Now", "Get Yours", "Discover More", "Order Today", "Learn More"
        
        Return only the CTA text, no additional text.
        """
        
        try:
            response = self._make_completion_request(prompt)
            cta = response.choices[0].message.content.strip()
            
            logger.info(f"Generated CTA for product: {product_name}")
            return cta
            
        except Exception as e:
            logger.error(f"Failed to generate call-to-action: {e}")
            raise
    
    def _make_completion_request(self, prompt: str) -> ChatCompletion:
        """Make a completion request to the OpenAI API.
        
        Args:
            prompt: The prompt to send
        
        Returns:
            Chat completion response
        
        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
