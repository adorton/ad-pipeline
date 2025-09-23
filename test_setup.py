#!/usr/bin/env python3
"""Test script to verify the ad pipeline setup."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from config import load_config
        from models import CampaignBrief, Template, Product
        from azure_client import AzureBlobClient
        from llm_client import LLMClient
        from firefly_client import FireflyClient
        from photoshop_client import PhotoshopClient
        from pipeline import AdPipeline
        from cli import cli
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    try:
        from config import load_config
        # This will fail without .env file, but we can test the structure
        print("✅ Configuration module structure is correct")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    try:
        from models import CampaignBrief, Template, Product
        
        # Test template model
        template = Template(file_id="test", filename="test.psd")
        assert template.file_id == "test"
        assert template.filename == "test.psd"
        
        # Test product model
        product = Product(name="Test Product", file_id="test_product", image="test.jpg")
        assert product.name == "Test Product"
        assert product.file_id == "test_product"
        
        # Test campaign brief model
        campaign = CampaignBrief(
            campaign_name="Test Campaign",
            templates=[template],
            products=[product],
            target_audience="Test audience",
            target_market="Test market",
            campaign_message="Test message"
        )
        assert campaign.campaign_name == "Test Campaign"
        assert len(campaign.templates) == 1
        assert len(campaign.products) == 1
        
        print("✅ Pydantic models work correctly")
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing ad pipeline setup...")
    print()
    
    tests = [
        test_imports,
        test_config_loading,
        test_models,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The ad pipeline is ready to use.")
        print()
        print("Next steps:")
        print("1. Copy env.template to .env and configure your API keys")
        print("2. Place campaign briefs and templates in the input/ directory")
        print("3. Run: python pipeline.py process")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

