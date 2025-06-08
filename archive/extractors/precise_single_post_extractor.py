#!/usr/bin/env python3
"""
Precise Single Post Extractor
Handle cookies popup and extract ONLY the main post with precise detection
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

def extract_precise_main_post(shortcode: str) -> Dict[str, Any]:
    """Extract precisely the main post only, handling popups"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # Keep visible to handle cookie popup
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    result = {
        "shortcode": shortcode,
        "main_post_images": [],
        "post_type": "unknown",
        "carousel_detected": False,
        "success": False
    }
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Precise extraction: {url}")
        driver.get(url)
        
        # Handle cookie popup
        print("🍪 Handling cookie popup...")
        try:
            # Wait for and handle cookie popup
            cookie_buttons = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Allow')]", 
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Decline')]",
                "[data-testid='cookie-banner-button']"
            ]
            
            for button_xpath in cookie_buttons:
                try:
                    cookie_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, button_xpath))
                    )
                    cookie_button.click()
                    print(f"   ✅ Clicked cookie button")
                    time.sleep(1)
                    break
                except:
                    continue
        except:
            print("   ℹ️ No cookie popup found")
        
        # Wait for main content to load
        time.sleep(5)
        
        # Strategy 1: Check for carousel navigation to determine post type
        print("🔍 Checking for carousel indicators...")
        
        carousel_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "button[aria-label*='Next'], button[aria-label*='Previous'], [aria-label*='Go to']")
        
        if carousel_buttons:
            result["carousel_detected"] = True
            result["post_type"] = "carousel"
            print(f"   🎠 CAROUSEL detected - found {len(carousel_buttons)} navigation buttons")
        else:
            result["carousel_detected"] = False
            result["post_type"] = "single"
            print(f"   📷 SINGLE POST detected - no navigation buttons")
        
        # Strategy 2: Get the main post container specifically
        # Look for the main content area, not the entire page
        main_content_selectors = [
            "article:first-of-type",  # First article (main post)
            "main article:first-child",  # First article in main
            "[role='presentation']:first-of-type article"  # First presentation article
        ]
        
        main_post_images = []
        
        for selector in main_content_selectors:
            try:
                main_container = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"   📄 Found main container with: {selector}")
                
                # Get images only from this container
                container_imgs = main_container.find_elements(By.CSS_SELECTOR, "img")
                
                for img in container_imgs:
                    src = img.get_attribute("src") or ""
                    alt = img.get_attribute("alt") or ""
                    
                    # Very strict filtering for main content
                    if ("fbcdn.net" in src and 
                        "t51.29350-15" in src and
                        not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                        
                        main_post_images.append({
                            "src": src,
                            "alt": alt,
                            "container": selector
                        })
                
                if main_post_images:
                    print(f"   ✅ Found {len(main_post_images)} images in main container")
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Container {selector} not found: {e}")
                continue
        
        # Strategy 3: For single posts, take only the first high-quality image
        if result["post_type"] == "single":
            # For single posts, we should have exactly 1 main image
            if main_post_images:
                result["main_post_images"] = main_post_images[:1]  # Take only first
                print(f"   📷 Single post: taking first image only")
            
        elif result["post_type"] == "carousel":
            # For carousels, try to detect the actual count
            page_source = driver.page_source
            carousel_count_match = re.search(r'"count":\s*(\d+)', page_source)
            
            if carousel_count_match:
                carousel_count = int(carousel_count_match.group(1))
                result["main_post_images"] = main_post_images[:carousel_count]
                print(f"   🎠 Carousel: taking {carousel_count} images")
            else:
                result["main_post_images"] = main_post_images
        
        result["success"] = len(result["main_post_images"]) > 0
        
        print(f"   ✅ Final: {result['post_type']} with {len(result['main_post_images'])} images")
        
        # Let user verify visually
        print(f"\\n👀 MANUAL VERIFICATION:")
        print(f"   Open: {url}")
        print(f"   Check: Is this actually a {result['post_type']} post?")
        print(f"   Expected: {len(result['main_post_images'])} image(s)")
        
        input("Press Enter after visual verification...")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        result["error"] = str(e)
        return result
    
    finally:
        driver.quit()

def test_precise_extraction():
    """Test precise extraction on the problematic shortcode"""
    
    shortcode = "C0xLaimIm1B"
    result = extract_precise_main_post(shortcode)
    
    print("\\n" + "="*60)
    print("🎯 PRECISE MAIN POST EXTRACTION RESULTS")
    print("="*60)
    print(f"Shortcode: {result['shortcode']}")
    print(f"Post Type: {result['post_type']}")
    print(f"Carousel Detected: {result['carousel_detected']}")
    print(f"Main images: {len(result['main_post_images'])}")
    print(f"Success: {result['success']}")
    
    if result['main_post_images']:
        print(f"\\n🖼️  MAIN POST IMAGES:")
        for i, img in enumerate(result['main_post_images'], 1):
            print(f"   {i}. {img['alt'][:80]}")
            print(f"      {img['src'][:80]}...")
            print(f"      Container: {img['container']}")
    
    if result.get('error'):
        print(f"\\n❌ Error: {result['error']}")

if __name__ == "__main__":
    test_precise_extraction()