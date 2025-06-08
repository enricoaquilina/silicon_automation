#!/usr/bin/env python3
"""
Test the fixed production extractor on the problematic shortcode
"""

import os
from production_instagram_extractor import ProductionInstagramExtractor

def test_fixed_extraction():
    """Test the fixed extraction on C0xFHGOrBN7"""
    
    shortcodes = ["C0xFHGOrBN7", "C0xLaimIm1B", "C0wmEEKItfR"]
    
    # Create extractor once for all tests
    extractor = ProductionInstagramExtractor(replicate_token='dummy')
    
    try:
        # Setup browser
        if not extractor.setup_browser():
            print("❌ Browser setup failed")
            return
        
        for shortcode in shortcodes:
            print(f"\n🧪 Testing fixed extraction on {shortcode}")
            print("=" * 60)
            
            try:
                # Extract image URLs
                image_urls = extractor.extract_image_urls(shortcode)
                
                print(f"\n📊 EXTRACTION RESULTS")
                print("=" * 40)
                print(f"Shortcode: {shortcode}")
                print(f"Images found: {len(image_urls)}")
                print(f"Success: {len(image_urls) > 0}")
                
                if image_urls:
                    print(f"\n🖼️  IMAGE URLS:")
                    for i, url in enumerate(image_urls, 1):
                        print(f"   {i}. {url[:80]}...")
                else:
                    print(f"\n❌ No images found")
                    
            except Exception as e:
                print(f"❌ Test failed for {shortcode}: {e}")
        
    except Exception as e:
        print(f"❌ Overall test failed: {e}")
    
    finally:
        if extractor.driver:
            extractor.driver.quit()

if __name__ == "__main__":
    test_fixed_extraction()