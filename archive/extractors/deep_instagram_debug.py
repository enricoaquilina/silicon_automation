#!/usr/bin/env python3
"""
Deep Instagram Debug
Comprehensive analysis of Instagram page structure to find correct patterns
"""

import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_instagram_structure():
    """Deep debug of Instagram page structure"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # NOT headless for debugging
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        shortcode = "C0xFHGOrBN7"
        url = f"https://www.instagram.com/p/{shortcode}/"
        
        print(f"🔍 Deep debugging: {url}")
        driver.get(url)
        time.sleep(10)  # Wait for full load
        
        page_source = driver.page_source
        
        # Save full page source for manual inspection
        with open("full_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("📄 Saved full page source to full_page_source.html")
        
        # Look for carousel indicators
        print("\\n🔍 CAROUSEL DETECTION:")
        carousel_patterns = [
            r'carousel',
            r'sidecar',
            r'edge_sidecar_to_children',
            r'"count":\s*(\d+)',
            r'GraphSidecar',
            r'__typename.*Sidecar'
        ]
        
        for pattern in carousel_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"   ✅ Found '{pattern}': {matches[:5]}")  # First 5 matches
            else:
                print(f"   ❌ Not found: '{pattern}'")
        
        # Look for JSON data
        print("\\n🔍 JSON DATA BLOCKS:")
        json_patterns = [
            r'window\._sharedData\s*=\s*({.*?});',
            r'window\.__additionalDataLoaded\s*=\s*({.*?});',
            r'"GraphImage".*?"display_url":"([^"]+)"',
            r'"GraphSidecar".*?"edge_sidecar_to_children"'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_source, re.DOTALL)
            if matches:
                print(f"   ✅ Found JSON pattern: {pattern[:30]}... ({len(matches)} matches)")
                if 'display_url' in pattern:
                    for match in matches[:3]:
                        print(f"      URL: {match[:60]}...")
            else:
                print(f"   ❌ No JSON: {pattern[:30]}...")
        
        # Analyze img elements in detail
        print("\\n🔍 IMG ELEMENTS ANALYSIS:")
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        print(f"Total img elements: {len(img_elements)}")
        
        content_images = []
        profile_images = []
        thumbnail_images = []
        other_images = []
        
        for i, img in enumerate(img_elements):
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if "fbcdn.net" in src:
                if "t51.29350-15" in src:  # Content images
                    content_images.append({"index": i, "src": src, "alt": alt})
                elif "t51.2885-19" in src:  # Profile images
                    profile_images.append({"index": i, "src": src, "alt": alt})
                elif any(size in src for size in ["s150x150", "s320x320"]):  # Thumbnails
                    thumbnail_images.append({"index": i, "src": src, "alt": alt})
                else:
                    other_images.append({"index": i, "src": src, "alt": alt})
        
        print(f"\\n📊 IMAGE CATEGORIZATION:")
        print(f"   Content images (t51.29350-15): {len(content_images)}")
        print(f"   Profile images (t51.2885-19): {len(profile_images)}")
        print(f"   Thumbnail images (s150x150, s320x320): {len(thumbnail_images)}")
        print(f"   Other images: {len(other_images)}")
        
        print(f"\\n🖼️  CONTENT IMAGES (likely carousel):")
        for img in content_images:
            print(f"   {img['index']}: {img['alt'][:50]}")
            print(f"      {img['src'][:80]}...")
        
        # Look for specific carousel navigation elements
        print("\\n🔍 CAROUSEL NAVIGATION ELEMENTS:")
        nav_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='Previous']", 
            "[role='button'][aria-label*='Next']",
            ".carousel",
            "[data-testid*='carousel']"
        ]
        
        for selector in nav_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Found navigation: {selector} ({len(elements)} elements)")
                else:
                    print(f"   ❌ No navigation: {selector}")
            except:
                print(f"   ❌ Error with selector: {selector}")
        
        print(f"\\n💡 RECOMMENDATIONS:")
        print(f"1. Focus on t51.29350-15 images (found {len(content_images)})")
        print(f"2. Filter by alt text containing post description")
        print(f"3. Use image resolution patterns to identify main images")
        print(f"4. Manual inspection of full_page_source.html for JSON structures")
        
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    debug_instagram_structure()