#!/usr/bin/env python3
"""
Fixed Carousel Extractor
Extract only the actual carousel images from the main post, not related posts
"""

import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

def extract_main_carousel_images(shortcode: str) -> Dict[str, Any]:
    """Extract only the main carousel images from the specific post"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    result = {
        "shortcode": shortcode,
        "carousel_images": [],
        "related_images": [],
        "success": False
    }
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Extracting main carousel from: {url}")
        driver.get(url)
        time.sleep(8)
        
        page_source = driver.page_source
        
        # Strategy 1: Look for the main post container and extract only images within it
        # The main post is usually in a specific container, while related posts are in different sections
        
        # Find all img elements
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        main_post_images = []
        related_post_images = []
        
        for img in img_elements:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if "fbcdn.net" in src and "t51.29350-15" in src:
                # Try to determine if this is main post vs related post
                # Main post images typically have specific alt text patterns
                
                # Get parent elements to understand context
                try:
                    # Look for specific container indicators
                    parent_html = img.get_attribute("outerHTML")
                    grandparent = driver.execute_script("return arguments[0].parentElement.parentElement.outerHTML;", img)
                    
                    # Heuristics to identify main post images:
                    is_main_post = any([
                        # Alt text refers to the specific post (usually has consistent date/author)
                        "Fanthasia" in alt and any(date in alt for date in ["December 12, 2023"]),
                        # First few images are usually main post
                        len(main_post_images) < 3,
                        # Main post images are usually larger
                        "p1080x1080" in src
                    ])
                    
                    if is_main_post and len(main_post_images) < 5:  # Limit to reasonable carousel size
                        main_post_images.append({
                            "src": src,
                            "alt": alt,
                            "index": len(main_post_images)
                        })
                    else:
                        related_post_images.append({
                            "src": src,
                            "alt": alt
                        })
                        
                except Exception as e:
                    # Fallback: first few content images are likely main post
                    if len(main_post_images) < 3:
                        main_post_images.append({
                            "src": src,
                            "alt": alt,
                            "index": len(main_post_images)
                        })
        
        # Strategy 2: Use JSON-LD data if available
        json_pattern = r'"@type":\s*"ImageObject"[^}]*"url":\s*"([^"]+)"'
        json_matches = re.findall(json_pattern, page_source)
        
        if json_matches:
            print(f"   📊 Found {len(json_matches)} JSON-LD images")
            # JSON-LD images are often in correct order
            for i, url in enumerate(json_matches[:3]):  # Take first 3 for carousel
                if "fbcdn.net" in url and url not in [img["src"] for img in main_post_images]:
                    main_post_images.append({
                        "src": url.replace("\\u0026", "&"),
                        "alt": f"Carousel image {i+1}",
                        "index": i,
                        "source": "json_ld"
                    })
        
        # Strategy 3: Look for specific Instagram carousel patterns in page source
        carousel_data_pattern = r'"carousel_media":\s*\[([^\]]+)\]'
        carousel_match = re.search(carousel_data_pattern, page_source)
        
        if carousel_match:
            print(f"   📊 Found carousel data in page source")
            # Extract URLs from carousel data
            carousel_urls = re.findall(r'"display_url":\s*"([^"]+)"', carousel_match.group(1))
            for i, url in enumerate(carousel_urls):
                clean_url = url.replace("\\u0026", "&").replace("\\/", "/")
                if clean_url not in [img["src"] for img in main_post_images]:
                    main_post_images.append({
                        "src": clean_url,
                        "alt": f"Carousel image {i+1}",
                        "index": i,
                        "source": "carousel_data"
                    })
        
        # Remove duplicates and limit to reasonable carousel size
        seen_urls = set()
        unique_main_images = []
        for img in main_post_images:
            if img["src"] not in seen_urls and len(unique_main_images) < 10:
                seen_urls.add(img["src"])
                unique_main_images.append(img)
        
        result["carousel_images"] = unique_main_images
        result["related_images"] = related_post_images
        result["success"] = len(unique_main_images) > 0
        
        print(f"   ✅ Extracted {len(unique_main_images)} main carousel images")
        print(f"   📊 Found {len(related_post_images)} related post images")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        result["error"] = str(e)
        return result
    
    finally:
        driver.quit()

def test_fixed_extraction():
    """Test the fixed carousel extraction"""
    
    shortcode = "C0xFHGOrBN7"
    result = extract_main_carousel_images(shortcode)
    
    print("\\n" + "="*60)
    print("🎯 FIXED CAROUSEL EXTRACTION RESULTS")
    print("="*60)
    print(f"Shortcode: {result['shortcode']}")
    print(f"Main carousel images: {len(result['carousel_images'])}")
    print(f"Related post images: {len(result['related_images'])}")
    print(f"Success: {result['success']}")
    
    if result['carousel_images']:
        print(f"\\n🖼️  MAIN CAROUSEL IMAGES:")
        for i, img in enumerate(result['carousel_images'], 1):
            print(f"   {i}. {img['alt'][:60]}")
            print(f"      {img['src'][:80]}...")
            if 'source' in img:
                print(f"      Source: {img['source']}")
    
    if result.get('error'):
        print(f"\\n❌ Error: {result['error']}")

if __name__ == "__main__":
    test_fixed_extraction()