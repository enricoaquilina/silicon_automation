#!/usr/bin/env python3
"""
Test Single Shortcode
Test the fixed extraction logic on a specific shortcode
"""

import asyncio
from production_instagram_extractor import ProductionInstagramExtractor

async def test_specific_shortcode():
    """Test extraction on a specific shortcode"""
    
    extractor = ProductionInstagramExtractor("")
    
    try:
        # Setup browser
        if not extractor.setup_browser():
            return
        
        # Test known single post shortcode
        shortcode = "C0xLaimIm1B"  # Known single post
        print(f"🔍 Testing shortcode: {shortcode}")
        
        # Extract URLs
        image_urls = extractor.extract_image_urls(shortcode)
        
        print(f"✅ Found {len(image_urls)} image URLs:")
        for i, url in enumerate(image_urls, 1):
            print(f"   {i}. {url[:80]}...")
    
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_specific_shortcode())