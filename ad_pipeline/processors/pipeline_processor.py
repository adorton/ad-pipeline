"""Main pipeline processor that orchestrates the entire ad generation workflow."""

import yaml
import requests
from pathlib import Path
from typing import List, Optional

from ..config.settings import Settings
from ..models.campaign import Campaign, Product, Template
from ..clients.azure_client import AzureBlobClient
from ..clients.llm_client import LLMClient
from ..clients.photoshop_client import PhotoshopClient
from ..clients.firefly_client import FireflyClient
from ..utils.file_utils import find_yaml_files, get_rendition_filename, ensure_directory
from ..utils.logging_utils import get_logger


logger = get_logger(__name__)


class PipelineProcessor:
    """Main processor that orchestrates the ad generation pipeline."""
    
    def __init__(self, settings: Settings):
        """Initialize the pipeline processor.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.azure_client = None
        self.llm_client = None
        self.photoshop_client = None
        self.firefly_client = None
        
        # Initialize clients
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize all required clients."""
        try:
            # Initialize Azure client if connection string is provided
            self.azure_client = AzureBlobClient(
                account_key=self.settings.azure_storage_account_key,
                account_name=self.settings.azure_storage_account_name,
                container_name=self.settings.azure_storage_container_name
            )
            logger.info("Azure Blob Storage client initialized")

            # Initialize LLM client
            self.llm_client = LLMClient(
                api_key=self.settings.llm_api_key,
                model=self.settings.llm_model,
                base_url=self.settings.llm_base_url,
                max_tokens=self.settings.llm_max_tokens,
                temperature=self.settings.llm_temperature
            )
            logger.info("LLM client initialized")

            # Initialize Photoshop client
            self.photoshop_client = PhotoshopClient(
                client_id=self.settings.ffs_client_id,
                client_secret=self.settings.ffs_secret
            )
            logger.info("Photoshop client initialized")
            
            # Initialize Firefly client
            self.firefly_client = FireflyClient(
                client_id=self.settings.ffs_client_id,
                client_secret=self.settings.ffs_secret
            )
            logger.info("Firefly client initialized")

        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
    
    def process_campaigns(self) -> None:
        """Process all campaign briefs in the input directory."""
        logger.info("Starting campaign processing pipeline")
        
        # Ensure directories exist
        self.settings.ensure_directories()
        
        # Find all YAML campaign files
        campaign_files = find_yaml_files(self.settings.input_directory)

        if not campaign_files:
            logger.warning(f"No YAML files found in input directory: {self.settings.input_directory}")
            return
        
        logger.info(f"Found {len(campaign_files)} campaign files to process")
        
        # Process each campaign file
        for campaign_file in campaign_files:
            try:
                self._process_campaign_file(campaign_file)
            except Exception as e:
                logger.error(f"Failed to process campaign file {campaign_file}: {e}")
                continue
        
        logger.info("Campaign processing pipeline completed")
    
    def _process_campaign_file(self, campaign_file: Path) -> None:
        """Process a single campaign file.
        
        Args:
            campaign_file: Path to the campaign YAML file
        """
        logger.info(f"Processing campaign file: {campaign_file.name}")
        
        # Load and validate campaign
        campaign = self._load_campaign(campaign_file)

        # Validate template files exist
        missing_templates = campaign.validate_template_files_exist(self.settings.input_directory)
        if missing_templates:
            logger.error(f"Missing template files: {missing_templates}")
            return

        # Validate product image files exist
        missing_images = campaign.validate_product_images_exist(self.settings.input_directory)
        if missing_images:
            logger.error(f"Missing product image files: {missing_images}")
            return

        # Create campaign directory in Azure storage
        campaign_dir = campaign_file.stem
        if self.azure_client:
            self._upload_templates_to_azure(campaign, campaign_dir)

        # Process each product
        for product in campaign.products:
            try:
                self._process_product(campaign, product, campaign_dir)
            except Exception as e:
                logger.error(f"Failed to process product {product.name}: {e}")
                continue

        logger.info(f"Successfully processed campaign: {campaign.campaign_name}")
    
    def _load_campaign(self, campaign_file: Path) -> Campaign:
        """Load and validate a campaign from YAML file.
        
        Args:
            campaign_file: Path to the campaign YAML file
        
        Returns:
            Loaded campaign object
        
        Raises:
            Exception: If loading or validation fails
        """
        try:
            with open(campaign_file, 'r', encoding=self.settings.file_encoding) as f:
                campaign_data = yaml.safe_load(f)
            
            campaign = Campaign(**campaign_data)
            logger.info(f"Successfully loaded campaign: {campaign.campaign_name}")
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to load campaign file {campaign_file}: {e}")
            raise
    
    def _upload_templates_to_azure(self, campaign: Campaign, campaign_dir: str) -> None:
        """Upload PSD templates to Azure storage.
        
        Args:
            campaign: Campaign object
            campaign_dir: Campaign directory name in Azure
        """
        if not self.azure_client:
            return
        
        for template in campaign.templates:
            template_path = self.settings.input_directory / template.filename
            blob_name = f"{campaign_dir}/{template.filename}"

            try:
                self.azure_client.upload_file(template_path, blob_name)
                logger.info(f"Uploaded template to Azure: {template.filename}")
            except Exception as e:
                logger.error(f"Failed to upload template {template.filename}: {e}")
                raise
    
    def _process_product(self, campaign: Campaign, product: Product, campaign_dir: str) -> None:
        """Process a single product for all templates.
        
        Args:
            campaign: Campaign object
            product: Product to process
            campaign_dir: Campaign directory name in Azure
        """
        logger.info(f"Processing product: {product.name}")
        
        # Get or generate product image
        product_image_path = self._get_product_image(product, campaign_dir)

        if product_image_path is None:
            logger.error(f"Failed to get image for product: {product.name}")
            return

        blob_name = f"{campaign_dir}/generated_{product.file_id}.png"
        self.azure_client.upload_file(product_image_path, blob_name)

        # Generate campaign messaging
        campaign_message = self._generate_campaign_message(campaign, product)
        cta_text = self._generate_cta_text(campaign, product, campaign_message)
        
        # Process each template
        for template in campaign.templates:
            try:
                self._process_template(
                    campaign, product, template, product_image_path.name,
                    campaign_message, cta_text, campaign_dir
                )
            except Exception as e:
                logger.error(f"Failed to process template {template.filename} for product {product.name}: {e}")
                continue
        
        logger.info(f"Successfully processed product: {product.name}")
    
    def _get_product_image(self, product: Product, campaign_dir: str) -> Optional[str]:
        """Get product image image. If one is not specified, this is where we generate it
        
        Args:
            product: Product object
            campaign_dir: Campaign directory name in Azure
        
        Returns:
            Image path
        """
        if product.has_image():
            # Load existing image file
            return self.settings.input_directory / product.image

        elif product.can_generate_image():
            # Generate image from prompt
            try:
                image_url = self.firefly_client.generate_product_image(
                    product_name=product.name,
                    prompt=product.prompt
                )

                generated_filename = f"generated_{product.file_id}.png"
                local_image_path = self._fetch_file(image_url, generated_filename, self.settings.temp_directory)

                logger.info(f"Generated product image for: {product.name}")

                return local_image_path
            except Exception as e:
                logger.error(f"Failed to generate image for product {product.name}: {e}")
                return None
        
        else:
            logger.error(f"Product {product.name} has no image or prompt")
            return None

    def _generate_campaign_message(self, campaign: Campaign, product: Product) -> str:
        """Generate tailored campaign message for a product.
        
        Args:
            campaign: Campaign object
            product: Product object
        
        Returns:
            Generated campaign message
        """
        try:
            message = self.llm_client.generate_campaign_message(
                base_message=campaign.campaign_message,
                target_audience=campaign.target_audience,
                target_market=campaign.target_market,
                product_name=product.name
            )
            logger.info(f"Generated campaign message for: {product.name}")
            return message
        except Exception as e:
            logger.error(f"Failed to generate campaign message for {product.name}: {e}")
            return campaign.campaign_message  # Fallback to base message
    
    def _generate_cta_text(self, campaign: Campaign, product: Product, campaign_message: str) -> str:
        """Generate call-to-action text for a product.
        
        Args:
            campaign: Campaign object
            product: Product object
            campaign_message: Generated campaign message
        
        Returns:
            Generated CTA text
        """
        try:
            cta = self.llm_client.generate_call_to_action(
                product_name=product.name,
                target_audience=campaign.target_audience,
                target_market=campaign.target_market,
                campaign_message=campaign_message
            )
            logger.info(f"Generated CTA for: {product.name}")
            return cta
        except Exception as e:
            logger.error(f"Failed to generate CTA for {product.name}: {e}")
            return "Shop Now"  # Fallback CTA
    
    def _process_template(
        self,
        campaign: Campaign,
        product: Product,
        template: Template,
        product_image_file: str,
        campaign_message: str,
        cta_text: str,
        campaign_dir: str
    ) -> None:
        """Process a single template for a product.
        
        Args:
            campaign: Campaign object
            product: Product object
            template: Template object
            product_image_file: Product image filename
            campaign_message: Generated campaign message
            cta_text: Generated CTA text
            campaign_dir: Campaign directory name in Azure
        """
        logger.info(f"Processing template {template.filename} for product {product.name}")
        
        # Load PSD template
        text_replace_input_url = self.azure_client.get_presigned_url(
            f"{campaign_dir}/{template.filename}"
        )
        text_replace_output_url = self.azure_client.get_presigned_url(
            f"{campaign_dir}/text_replace/{template.filename}"
        )

        # Replace text layers
        text_replace_output_url = self.photoshop_client.replace_text(
            text_replace_input_url,
            text_replace_output_url,
            [("campaign_text", campaign_message), ("cta_text", cta_text)],
        )

        # Process product image
        product_image_url = self.azure_client.get_presigned_url(
            f"{campaign_dir}/{product_image_file}"
        )

        image_remove_bg_url = self.photoshop_client.remove_background(product_image_url)

        final_psd_url = self.azure_client.get_presigned_url(
            f"{campaign_dir}/final_template/{template.filename}"
        )

        # Replace smart object with product image
        psd_data = self.photoshop_client.replace_smart_object(
            text_replace_output_url, "product_photo", image_remove_bg_url, final_psd_url
        )

        rendition_filename = f"{template.file_id}_{product.file_id}.png"
        rendition_url = self.azure_client.get_presigned_url(
            f"{campaign_dir}/final_rendition/{rendition_filename}"
        )

        # Create rendition
        rendition_url = self.photoshop_client.create_rendition(final_psd_url, rendition_url, "image/png")

        local_directory = self.settings.output_directory / campaign_dir

        # Save rendition locally
        self._fetch_file(rendition_url, rendition_filename, local_directory)

        logger.info(f"Successfully created rendition: {product.file_id}_{template.file_id}.png")
    
    def _save_rendition(
        self,
        rendition_data: bytes,
        campaign: Campaign,
        product: Product,
        template: Template
    ) -> None:
        """Save rendition to local output directory.
        
        Args:
            rendition_data: Rendered image data
            campaign: Campaign object
            product: Product object
            template: Template object
        """
        # Create campaign output directory
        campaign_output_dir = self.settings.output_directory / campaign.campaign_name
        ensure_directory(campaign_output_dir)
        
        # Generate filename
        filename = get_rendition_filename(product.file_id, template.file_id)
        output_path = campaign_output_dir / filename
        
        # Save file
        with open(output_path, 'wb') as f:
            f.write(rendition_data)
        
        logger.info(f"Saved rendition: {output_path}")
    
    def _upload_rendition_to_azure(
        self,
        rendition_data: bytes,
        campaign: Campaign,
        product: Product,
        template: Template,
        campaign_dir: str
    ) -> None:
        """Upload rendition to Azure storage.
        
        Args:
            rendition_data: Rendered image data
            campaign: Campaign object
            product: Product object
            template: Template object
            campaign_dir: Campaign directory name in Azure
        """
        if not self.azure_client:
            return
        
        filename = get_rendition_filename(product.file_id, template.file_id)
        blob_name = f"{campaign_dir}/renditions/{filename}"
        
        try:
            self.azure_client.upload_data(rendition_data, blob_name)
            logger.info(f"Uploaded rendition to Azure: {filename}")
        except Exception as e:
            logger.error(f"Failed to upload rendition {filename}: {e}")

    def _fetch_file(self, url: str, filename: str, target_dir: Path) -> Path:
        """Fetch an asset from a presigned or publically accessible URL and
           save the binary data to a file
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        response = requests.get(url)
        response.raise_for_status()

        file_bytes = response.content
        with open(target_path, 'wb') as f:
            f.write(file_bytes)
        return target_path
