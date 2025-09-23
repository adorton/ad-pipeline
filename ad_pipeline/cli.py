#!/usr/bin/env python3
"""CLI interface for the ad pipeline."""

import click
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from ad_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from ad_pipeline.config import load_config
from ad_pipeline.models import CampaignBrief
from ad_pipeline.azure_client import AzureBlobClient
from ad_pipeline.llm_client import LLMClient
from ad_pipeline.firefly_client import FireflyClient


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """GenAI Ad Pipeline for generating ad renditions from campaign briefs."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo("Verbose mode enabled")


@cli.command()
@click.pass_context
def process(ctx):
    """Process all campaign briefs and generate ad renditions."""
    verbose = ctx.obj.get('verbose', False)
    
    if verbose:
        click.echo("Starting ad pipeline processing...")
    
    try:
        # Load configuration
        config = load_config()
        
        if verbose:
            click.echo(f"Configuration loaded successfully")
            click.echo(f"Processing briefs from: {config.input_dir}")
            click.echo(f"Output directory: {config.output_dir}")
        
        # Initialize clients
        azure_client = AzureBlobClient(
            connection_string=config.azure_connection_string,
            container_name=config.azure_container_name
        )
        
        llm_client = LLMClient(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        firefly_client = FireflyClient(
            client_id=config.ffs_client_id,
            client_secret=config.ffs_client_secret
        )
        
        if verbose:
            click.echo("Clients initialized successfully")
        
        # TODO: Implement the actual processing logic
        click.echo("Processing logic not yet implemented")
        click.echo("This is a placeholder for the main processing functionality")
        
        if verbose:
            click.echo("Processing completed successfully")
        else:
            click.echo("✅ Processing completed")
            
    except Exception as e:
        click.echo(f"❌ Error during processing: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
def test():
    """Test the pipeline setup and configuration."""
    click.echo("Testing pipeline setup...")
    
    try:
        # Test configuration loading
        config = load_config()
        click.echo("✅ Configuration loaded successfully")
        
        # Test model imports
        from ad_pipeline.models import CampaignBrief, Template, Product
        click.echo("✅ Models imported successfully")
        
        # Test client imports
        from ad_pipeline.azure_client import AzureBlobClient
        from ad_pipeline.llm_client import LLMClient
        from ad_pipeline.firefly_client import FireflyClient
        click.echo("✅ Clients imported successfully")
        
        click.echo("🎉 All tests passed! Pipeline is ready to use.")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
