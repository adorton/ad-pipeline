"""LLM client for OpenAI API calls."""

import logging
from typing import Optional

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM operations using OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize the LLM client."""
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
        original_message: str,
        target_audience: str,
        target_market: str
    ) -> str:
        """Generate tailored campaign message for target audience and market."""
        prompt = f"""
        You are a marketing expert. Please tailor the following campaign message for the specified target audience and market.
        
        Original campaign message: "{original_message}"
        Target audience: {target_audience}
        Target market: {target_market}
        
        Please provide a tailored version of the campaign message that:
        1. Appeals to the target audience
        2. Is appropriate for the target market
        3. Maintains the core message but adapts the tone and language
        4. Is concise and impactful
        
        Return only the tailored message, no additional commentary.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a marketing expert specializing in campaign message optimization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            tailored_message = response.choices[0].message.content.strip()
            logger.info("Generated tailored campaign message")
            return tailored_message
            
        except Exception as e:
            logger.error(f"Failed to generate campaign message: {e}")
            raise
    
    def generate_call_to_action(
        self,
        campaign_message: str,
        target_audience: str,
        target_market: str
    ) -> str:
        """Generate call-to-action text for the campaign."""
        prompt = f"""
        You are a marketing expert. Please generate a compelling call-to-action (CTA) for the following campaign.
        
        Campaign message: "{campaign_message}"
        Target audience: {target_audience}
        Target market: {target_market}
        
        Please provide a call-to-action that:
        1. Is appropriate for the target audience and market
        2. Creates urgency or excitement
        3. Is clear and actionable
        4. Is concise (1-4 words typically)
        5. Matches the tone of the campaign message
        
        Examples of good CTAs: "Shop Now", "Get Yours", "Learn More", "Buy Today", "Discover More"
        
        Return only the call-to-action text, no additional commentary.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a marketing expert specializing in call-to-action optimization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            cta = response.choices[0].message.content.strip()
            logger.info("Generated call-to-action")
            return cta
            
        except Exception as e:
            logger.error(f"Failed to generate call-to-action: {e}")
            raise

