#!/usr/bin/env python3
"""Example usage of the ad pipeline."""

from ad_pipeline.config.settings import Settings
from ad_pipeline.processors.pipeline_processor import PipelineProcessor
from ad_pipeline.utils.logging_utils import setup_logging


def main():
    """Example of how to use the ad pipeline programmatically."""
    # Set up logging
    logger = setup_logging(level="INFO")
    
    try:
        # Load settings
        settings = Settings.load()
        logger.info("Settings loaded successfully")
        
        # Create pipeline processor
        processor = PipelineProcessor(settings)
        
        # Process campaigns
        processor.process_campaigns()
        
        logger.info("Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
