#!/usr/bin/env python3
"""
Compare Extractors
Compare working fixed extractor vs production to identify the issue
"""

from fixed_carousel_extractor import extract_main_carousel_images
import re

def test_comparison():
    """Compare both extraction methods"""
    
    shortcode = "C0xLaimIm1B"  # One that failed in production
    
    print("🔍 COMPARING EXTRACTION METHODS")
    print("="*50)
    
    # Test working fixed extractor
    print("\\n1️⃣ TESTING FIXED EXTRACTOR:")
    result = extract_main_carousel_images(shortcode)
    
    print(f"   Success: {result['success']}")
    print(f"   Main images: {len(result['carousel_images'])}")
    print(f"   Related images: {len(result['related_images'])}")
    
    if result['carousel_images']:
        print("   📸 Main carousel URLs:")
        for i, img in enumerate(result['carousel_images'], 1):
            print(f"      {i}. {img['src'][:80]}...")
    
    # Now let's see what patterns would match these URLs
    if result['carousel_images']:
        test_url = result['carousel_images'][0]['src']
        print(f"\\n2️⃣ TESTING PATTERNS ON WORKING URL:")
        print(f"   Test URL: {test_url[:80]}...")
        
        patterns = [
            r'"display_url":"([^"]+fbcdn\.net[^"]+t51\.29350-15[^"]*)"',
            r'"src":"([^"]+fbcdn\.net[^"]+t51\.29350-15[^"]*)"',
            r'src="([^"]+fbcdn\.net[^"]+t51\.29350-15[^"]*)"',
            r'"display_url":"([^"]+)"',
            r'"src":"([^"]+fbcdn\.net[^"]+)"',
            r'src="([^"]+fbcdn\.net[^"]+)"'
        ]
        
        # Test each pattern against a mock page source containing the URL
        mock_page_source = f'"display_url":"{test_url}","src":"{test_url}"'
        
        for pattern in patterns:
            matches = re.findall(pattern, mock_page_source)
            print(f"   Pattern: {pattern[:40]}...")
            print(f"   Matches: {len(matches)}")
            if matches:
                print(f"      {matches[0][:60]}...")
        
        # Check what identifiers the working URL has
        print(f"\\n3️⃣ URL ANALYSIS:")
        print(f"   Contains 'fbcdn.net': {'fbcdn.net' in test_url}")
        print(f"   Contains 't51.29350-15': {'t51.29350-15' in test_url}")
        print(f"   Contains 'p1080x1080': {'p1080x1080' in test_url}")
        print(f"   Contains '.jpg': {'.jpg' in test_url}")

if __name__ == "__main__":
    test_comparison()