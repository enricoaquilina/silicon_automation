#!/usr/bin/env python3
"""
Final Instagram Extractor
Wait for dynamic content to load and extract actual visible images like 4K Stogram
"""

import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

def extract_dynamic_carousel(shortcode: str) -> Dict[str, Any]:
    """Extract carousel by waiting for dynamic content to fully load"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # Keep visible to see what's happening
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    result = {
        "shortcode": shortcode,
        "carousel_images": [],
        "post_type": "unknown",
        "carousel_count": 0,
        "success": False
    }
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        
        # Handle cookie popup
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
            )
            cookie_button.click()
            time.sleep(2)
            print("   🍪 Handled cookie popup")
        except:
            print("   ℹ️ No cookie popup")
        
        # Wait for images to actually load (this is key!)
        print("   ⏳ Waiting for images to load...")
        time.sleep(10)  # Give Instagram time to load images
        
        # Strategy 1: Look for actual loaded img elements with content
        print("   🔍 Looking for loaded images...")
        
        # Find all img elements that have actually loaded
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        content_images = []
        
        for img in img_elements:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            # Look for high-quality content images that have loaded
            if ("fbcdn.net" in src and 
                "t51.29350-15" in src and  # Content image identifier
                not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar']) and
                "Photo by" in alt):  # Actual post content
                
                content_images.append({
                    "src": src,
                    "alt": alt,
                    "index": len(content_images)
                })
        
        print(f"   📊 Found {len(content_images)} content images")
        
        # Strategy 2: Check for carousel navigation to determine actual post type
        carousel_nav = driver.find_elements(By.CSS_SELECTOR, 
            "button[aria-label*='Next'], button[aria-label*='Go to'], [role='button'][aria-label*='Next']")
        
        if carousel_nav:
            result["post_type"] = "carousel"
            print("   🎠 Carousel detected (has navigation)")
            
            # For carousel, get unique images by filtering similar alt text
            unique_images = []
            seen_alts = set()
            
            for img in content_images:
                # Use the main part of alt text to identify unique images
                alt_key = img["alt"].split(" on ")[0] if " on " in img["alt"] else img["alt"]
                if alt_key not in seen_alts:
                    seen_alts.add(alt_key)
                    unique_images.append(img)
            
            result["carousel_images"] = unique_images
            result["carousel_count"] = len(unique_images)
            
        else:
            result["post_type"] = "single"
            print("   📷 Single post detected")
            
            # For single post, take the first content image
            if content_images:
                result["carousel_images"] = content_images[:1]
                result["carousel_count"] = 1
        
        result["success"] = len(result["carousel_images"]) > 0
        
        print(f"   ✅ Final: {result['post_type']} with {len(result['carousel_images'])} images")
        
        # Let user see the browser for verification
        print(f"\\n👀 MANUAL VERIFICATION:")
        print(f"   Browser is open - you can see what images are actually loaded")
        print(f"   Expected: Check if this matches the actual post")
        
        input("Press Enter after verification...")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        result["error"] = str(e)
        return result
    
    finally:
        driver.quit()

def test_dynamic_extraction():
    """Test dynamic extraction on our problem shortcodes"""
    
    test_cases = [
        ("C0xFHGOrBN7", 3),   # Should be 3 carousel
        ("C0xLaimIm1B", 1),   # Should be 1 single
        ("C0wmEEKItfR", 10),  # Should be 10 carousel
    ]
    
    print("🎯 DYNAMIC EXTRACTION TEST (4K Stogram Style)")
    print("=" * 60)
    
    for shortcode, expected in test_cases:
        print(f"\\n📋 Testing {shortcode} (expected: {expected})")
        print("─" * 40)
        
        result = extract_dynamic_carousel(shortcode)
        
        actual = len(result["carousel_images"])
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} Expected: {expected}, Got: {actual}")
        print(f"   Post type: {result['post_type']}")
        print(f"   Success: {result['success']}")
        
        if result["carousel_images"]:
            print(f"   📸 Images:")
            for img in result["carousel_images"]:
                print(f"      {img['index']}: {img['alt'][:50]}...")
                print(f"         {img['src'][:60]}...")
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")
        
        # Ask user to confirm
        user_input = input(f"\\nDoes this look correct for {shortcode}? (y/n): ")
        if user_input.lower() != 'y':
            print("❌ User says this is incorrect")
        else:
            print("✅ User confirmed this is correct")

if __name__ == "__main__":
    test_dynamic_extraction()