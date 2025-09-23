"""Command-line interface for the ad pipeline."""

import sys
from pathlib import Path

import click

from ad_pipeline.config.settings import Settings
from ad_pipeline.processors.pipeline_processor import PipelineProcessor
from ad_pipeline.utils.logging_utils import setup_logging


@click.group()
@click.option(
    '--log-level',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    help='Set the logging level'
)
@click.option(
    '--log-file',
    type=click.Path(),
    help='Optional log file path'
)
@click.pass_context
def cli(ctx, log_level, log_file):
    """GenAI Ad Pipeline - Generate advertising campaigns from briefs."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Set up logging
    logger = setup_logging(
        level=log_level,
        log_file=Path(log_file) if log_file else None
    )
    
    # Store logger in context
    ctx.obj['logger'] = logger
    
    # Load settings
    try:
        settings = Settings.load()
        ctx.obj['settings'] = settings
        logger.info("Settings loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def process(ctx):
    """Process all campaign briefs in the input directory."""
    logger = ctx.obj['logger']
    settings = ctx.obj['settings']
    
    logger.info("Starting ad pipeline processing")
    
    try:
        # Create pipeline processor
        processor = PipelineProcessor(settings)
        
        # Process campaigns
        processor.process_campaigns()
        
        logger.info("Ad pipeline processing completed successfully")
        click.echo("✅ Campaign processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        click.echo(f"❌ Pipeline processing failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    '--campaign-file',
    type=click.Path(exists=True, path_type=Path),
    help='Path to a specific campaign file to process'
)
@click.pass_context
def validate(ctx, campaign_file):
    """Validate campaign brief files."""
    logger = ctx.obj['logger']
    settings = ctx.obj['settings']
    
    from ad_pipeline.models.campaign import Campaign
    import yaml
    
    if campaign_file:
        # Validate specific file
        campaign_files = [campaign_file]
    else:
        # Find all YAML files
        from ad_pipeline.utils.file_utils import find_yaml_files
        campaign_files = find_yaml_files(settings.input_directory)
    
    if not campaign_files:
        click.echo("No campaign files found to validate")
        return
    
    all_valid = True
    
    for campaign_file in campaign_files:
        try:
            with open(campaign_file, 'r', encoding=settings.file_encoding) as f:
                campaign_data = yaml.safe_load(f)
            
            campaign = Campaign(**campaign_data)
            
            # Validate template files exist
            missing_templates = campaign.validate_template_files_exist(settings.input_directory)
            if missing_templates:
                click.echo(f"❌ {campaign_file.name}: Missing template files: {missing_templates}")
                all_valid = False
                continue
            
            # Validate product image files exist
            missing_images = campaign.validate_product_images_exist(settings.input_directory)
            if missing_images:
                click.echo(f"❌ {campaign_file.name}: Missing product image files: {missing_images}")
                all_valid = False
                continue
            
            click.echo(f"✅ {campaign_file.name}: Valid campaign brief")
            
        except Exception as e:
            click.echo(f"❌ {campaign_file.name}: Validation failed - {e}")
            all_valid = False
    
    if all_valid:
        click.echo("🎉 All campaign files are valid!")
    else:
        click.echo("⚠️  Some campaign files have validation errors")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    settings = ctx.obj['settings']
    
    click.echo("Current Configuration:")
    click.echo("=" * 50)
    click.echo(f"Input Directory: {settings.input_directory}")
    click.echo(f"Output Directory: {settings.output_directory}")
    click.echo(f"File Encoding: {settings.file_encoding}")
    click.echo(f"LLM Provider: {settings.llm_provider}")
    click.echo(f"LLM Model: {settings.llm_model}")
    click.echo(f"LLM Max Tokens: {settings.llm_max_tokens}")
    click.echo(f"LLM Temperature: {settings.llm_temperature}")
    click.echo(f"Azure Container: {settings.azure_storage_container}")
    click.echo(f"Azure Storage: {'Configured' if settings.azure_storage_connection_string else 'Not configured'}")


@cli.command()
@click.pass_context
def list_campaigns(ctx):
    """List all campaign files in the input directory."""
    settings = ctx.obj['settings']
    
    from ad_pipeline.utils.file_utils import find_yaml_files
    
    campaign_files = find_yaml_files(settings.input_directory)
    
    if not campaign_files:
        click.echo("No campaign files found in input directory")
        return
    
    click.echo(f"Found {len(campaign_files)} campaign files:")
    for campaign_file in campaign_files:
        click.echo(f"  - {campaign_file.name}")


if __name__ == '__main__':
    cli()
