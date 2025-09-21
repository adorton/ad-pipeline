# GenAI Ad Pipeline

## Overview

* Read one or more campaign briefs in a structured format (YAML). These files
  contain product images, messaging details, target audience/market, etc.
* For each campaign brief, generate ad image renditions from a given set of
  product images and Photoshop templates.
* Input and output files are stored locally.
* For Firefly Services (FFS) API calls, Azure blob storage will be used to store
  transient asssets.
* Use an LLM to tailor campaign messaging and call-to-action (OpenAI only for
  now)

## Setup

This is a Python 3.13 application that uses [uv](https://docs.astral.sh/uv/) to
manage dependencies, the Python environment, runtime, etc. Configuration is
handled with a `.env` file.

1. Install uv (if needed)
   
   Linux/macOS
   
   ```
   $ curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   
   Windows
   
   ```
   > powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. In the project directory, set up the virtual environment and install
   dependencies

   ```
   $ uv sync
   ```
   
3. Create enviroment file. This is where you will configure your input
   directory, output directory, logging, API keys, etc.

   ```
   $ cp env.template .env
   ```

## Configuration

Exmaple:

``` sh
# API Credentials
FFS_CLIENT_ID=8ef6...1596
FFS_SECRET=p8e-...Qzxy

# LLM Credentials and Config
LLM_PROVIDER=openai
LLM_API_KEY=sk-...mhQA
LLM_MODEL=gpt-3.5-turbo
LLM_BASE_URL=
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7

# Application Config
INPUT_DIRECTORY=./input
OUTPUT_DIRECTORY=./output
FILE_ENCODING=utf-8
```

* `FFS_CLIENT_ID` - Client ID for Firefly and Photoshop APIs
* `FFS_SECRET` - Client ID for Firefly and Photoshop APIs
* `LLM_PROVIDER` - Should be `openai` since that is currently the only supported
  LLM
* `LLM_API_KEY` - API key for LLM
* `LLM_MODEL` - The LLM model to use
* `LLM_BASE_URL` - Base URL for LLM (optional)
* `LLM_MAX_TOKENS` - Max tokens to use in LLM API calls
* `LLM_TEMPERATURE` - LLM temperature
* `INPUT_DIRECTORY` - Directory where the inputs (campaign files, templates,
  product photos) can be found
* `OUTPUT_DIRECTORY` - Directory where final campaign image renditions are
  placed
* `FILE_ENCODING` - File encoding of campaign YAML files

## Inputs

* **Campaign Brief** - A YAML file that contains the following details. It
  should be placed in the input directory alongside template and product photo
  files. See [the example brief](example-inputs/example-brief.yml).
  * `campaign_name` - Friendly name for campaign used in logging and email
    alerts.
  * `templates` - List of the filenames of the PSD templates to use. These
    should be placed in the input directory alongside the campaign brief file.
    The application will log an error and exit if any of the PSD template files
    are not found.
  * `products` - List of product definitions.
    * `name` - Product name
    * `image` - Product image to use in the PSD template. If this field is
      blank, the `prompt` field will be used to generate an image. If a filename
      is specified here and the file cannot be found, an error will be logged
      and the product will be skipped.
  * `target_audience` - A brief description of the target audience (age, gender,
    ethnicity and other demographic information).
  * `target_market` - Brief description of the geographic locale and/or target
    market (country, city, local language, etc).
  * `campaign_message` - The campaign message that will be run through an LLM in
    order to tailor it to the target audience and target market, translating to
    the target language and locale if needed.
* **PSD Template Files** - One or more PSD (Photoshop Document) files, each
  containing a placeholder smart object for the product photo, a text layer for
  campaign verbiage and another text layer for call to action (e.g. "Buy Now").
* **Product Images** - One or more image files (jpg or png) of the products in
  the campaign. These will be inserted into the PSD templates.

## Running the Pipeline

The command to run the pipeline is:

``` sh
$ uv run pipeline.py process
```

### Available Commands

- `process` - Process all campaign briefs and generate ad renditions
- `validate` - Validate campaign briefs and check for required files
- `--help` - Show help information
- `--verbose` / `-v` - Enable verbose logging

### Examples

``` sh
# Process all campaigns
$ uv run pipeline.py process

# Process with verbose logging
$ uv run pipeline.py --verbose process

# Validate campaign briefs
$ uv run pipeline.py validate

# Validate with custom directories
$ uv run pipeline.py validate --input-dir ./my-campaigns --output-dir ./my-output
```

When the pipeline runs, it follows this general workflow:

1. Get a list of `.yml` files from the input directory (e.g. `inputs/*.yml`)
2. For each campaign file (e.g. `my-campaign-brief.yml`):
   1. Load and validate campaign file
   2. Ensure PSD templates all exist. If any PSD template files don't exist in the
   input directory, then log error and exit.
   3. Ensure all PSD template definitions have a `file_id` - this is used in the
   final rendition naming convention.
   4. Create directory in Azure blob storage repository. Directory will have the
   name of the campaign file (e.g. `campaign.yml`).
   5. Upload PSD templates to campaign directory in Azure storage.
   6. For each product definition:
      1. If the `file_id` of the product is not specified, log error and continue
          to next product.
      2. If product image is specified and is found in input directory, then upload
          to campaign folder in Azure storage.
      3. If the product image is specified but not found, log error and continue to
          next product.
      4. If product image filename is not specified, then use `prompt` to generate
          product image from Firefly API.
      5. If prompt is also blank, then log error and continue to next product.
      6. Send a prompt request to the ChatGPT API to get campaign verbiage for the
          template.
      7. Send a prompt request to the ChatGPT API to get call-to-action text.
      8. For each PSD template:
          1. Send Photoshop API request to replace text endpoint to replace the
              campaign verbiage and call-to-action layers with text generated from
              the LLM call.
          2. Run product image through the product crop Photoshop API.
          3. Run croppped product image through the "remove background" Photoshop API.
          4. Send Photoshop API request to Replace Smart Object endpoint to insert
              the product photo into the PSD template.
          5. Run final PSD through the "create rendition" Photoshop API to create a
              png.
          6. Download the rendition from the Azure campaign directory and write the
              file to the `{output}/{campaign}` directory where `{campaign}` has the
              same name as the campaign brief file and `{output}` is the output
              container directory. For example, is the brief file is
              `summer-sale.yml` and all outputs go into the directory `output`, then
              outputs will be placed in the directory `output/summer-sale.yml/`.
          7. Rendition should have the naming convention
              `{product_file_id}_{template_file_id}.png` where `product_file_id` is
              the `file_id` of the product and `template_file_id` is the `file_id` of
              the template.
          8. Log message that rendition was created successfully.
      9. When all renditions are created successfully, log a success message.
   7. When all renditions are finished for the campaign, log a success message.
3. When process completes, log an overall success message.

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all required API keys are set in your `.env` file
2. **Missing Template Files**: Use the `validate` command to check for missing PSD templates
3. **Azure Storage Issues**: Verify your Azure storage account credentials and container permissions
4. **API Rate Limits**: The pipeline includes error handling for rate limits, but you may need to add delays for high-volume processing

### Validation

Before running the pipeline, use the validate command to check your setup:

``` sh
$ uv run pipeline.py validate
```

This will:
- Check that all YAML files are valid
- Verify that PSD templates exist
- Check for missing product images
- Display a summary of your campaigns

### Logging

Enable verbose logging to see detailed information about the processing:

``` sh
$ uv run pipeline.py --verbose process
```

### File Structure Requirements

- Campaign briefs must be valid YAML files
- PSD templates must exist in the input directory
- Product images are optional if you provide prompts
- All file paths are case-sensitive

## Development

### Testing

Run the test script to verify your setup:

``` sh
$ python test_setup.py
```

### Project Structure

```
ad-pipeline/
├── ad_pipeline/            # Source code
│   ├── __init__.py
│   ├── cli.py             # CLI interface
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models
│   ├── azure_client.py    # Azure Blob Storage client
│   ├── llm_client.py      # OpenAI LLM client
│   ├── firefly_client.py  # Adobe Firefly client
│   ├── photoshop_client.py # Adobe Photoshop API client
│   └── pipeline.py        # Main pipeline processor
├── input/                 # Input files directory
├── output/                # Output files directory
├── example-inputs/        # Example campaign briefs
├── pipeline.py           # Main entry point
├── test_setup.py         # Setup verification script
├── pyproject.toml        # Project configuration
├── env.template          # Environment template
└── README.md             # This file
```
