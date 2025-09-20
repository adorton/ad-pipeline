# GenAI Ad Pipeline

## Overview

1. 

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

# Application Config
INPUT_DIRECTORY=./input
OUTPUT_DIRECTORY=./output
FILE_ENCODING=utf-8
```

Notes:

* Firefly Services (FFS) credentials are used for all Firefly and Photoshop API
  calls

## Inputs

* **Campaign Brief** - A YAML file that contains the following details. It
  should be placed in the input directory alongside template and product photo
  files. See [example-inputs/example-brief.yml](the example brief).
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
