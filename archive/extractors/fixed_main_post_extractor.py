#!/usr/bin/env python3
"""
Fixed Main Post Extractor
Extract ONLY the main post images, excluding related/recommended posts
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

def extract_main_post_only(shortcode: str) -> Dict[str, Any]:
    """Extract only the main post images, not related posts"""
    
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
        "main_post_images": [],
        "related_images": [],
        "post_type": "unknown",
        "success": False
    }
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Extracting main post only: {url}")
        driver.get(url)
        time.sleep(6)
        
        # Strategy 1: Find the main article container
        # The main post is usually in the first article element
        try:
            # Look for the main article container
            main_articles = driver.find_elements(By.CSS_SELECTOR, "article")
            
            if main_articles:
                main_article = main_articles[0]  # First article is the main post
                print(f"   📄 Found main article container")
                
                # Get images ONLY from the main article
                main_imgs = main_article.find_elements(By.CSS_SELECTOR, "img")
                
                main_post_urls = []
                for img in main_imgs:
                    src = img.get_attribute("src") or ""
                    alt = img.get_attribute("alt") or ""
                    
                    # Filter for content images only
                    if ("fbcdn.net" in src and 
                        "t51.29350-15" in src and
                        not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile'])):
                        
                        main_post_urls.append({
                            "src": src,
                            "alt": alt,
                            "source": "main_article"
                        })
                
                print(f"   📊 Found {len(main_post_urls)} images in main article")
                
                # Check for carousel indicators within main article
                carousel_indicators = main_article.find_elements(By.CSS_SELECTOR, 
                    "button[aria-label*='Next'], button[aria-label*='Previous'], [role='button'][aria-label*='Next']")
                
                if carousel_indicators:
                    result["post_type"] = "carousel"
                    print(f"   🎠 Carousel detected (navigation found)")
                else:
                    result["post_type"] = "single"
                    print(f"   📷 Single post detected")
                
                result["main_post_images"] = main_post_urls
                
        except Exception as e:
            print(f"   ⚠️ Main article extraction failed: {e}")
        
        # Strategy 2: Use position-based filtering
        # Main post images are typically the first few content images
        if not result["main_post_images"]:
            print(f"   🔄 Fallback: position-based filtering")
            
            all_imgs = driver.find_elements(By.CSS_SELECTOR, "img")
            content_images = []
            
            for img in all_imgs:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                if ("fbcdn.net" in src and 
                    "t51.29350-15" in src and
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile'])):
                    
                    content_images.append({
                        "src": src,
                        "alt": alt,
                        "source": "position_based"
                    })
            
            # For single posts, take only the first content image
            # For carousels, take first few (but limit to reasonable number)
            page_source = driver.page_source
            carousel_count_match = re.search(r'"count":\s*(\d+)', page_source)
            
            if carousel_count_match:
                carousel_count = min(int(carousel_count_match.group(1)), 10)
                if carousel_count > 1:
                    result["post_type"] = "carousel"
                    result["main_post_images"] = content_images[:carousel_count]
                else:
                    result["post_type"] = "single"
                    result["main_post_images"] = content_images[:1]
            else:
                # Default to single post
                result["post_type"] = "single"
                result["main_post_images"] = content_images[:1]
            
            print(f"   📊 Fallback found {len(result['main_post_images'])} main images")
        
        # Strategy 3: Filter by alt text consistency
        # Main post images should have similar alt text (same date/author)
        if len(result["main_post_images"]) > 1:
            print(f"   🔍 Filtering by alt text consistency...")
            
            # Group by date mentioned in alt text
            from collections import defaultdict
            date_groups = defaultdict(list)
            
            for img in result["main_post_images"]:
                alt = img["alt"]
                # Extract dates from alt text
                date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                if date_matches:
                    date = date_matches[0]
                    date_groups[date].append(img)
                else:
                    date_groups["unknown"].append(img)
            
            # Take the largest group (likely the main post)
            if date_groups:
                main_date = max(date_groups.keys(), key=lambda k: len(date_groups[k]))
                main_images = date_groups[main_date]
                
                print(f"   📅 Filtered to {len(main_images)} images with consistent date: {main_date}")
                result["main_post_images"] = main_images
                
                # Store other images as related
                for date, imgs in date_groups.items():
                    if date != main_date:
                        result["related_images"].extend(imgs)
        
        result["success"] = len(result["main_post_images"]) > 0
        
        print(f"   ✅ Final result: {result['post_type']} with {len(result['main_post_images'])} main images")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        result["error"] = str(e)
        return result
    
    finally:
        driver.quit()

def test_main_post_extraction():
    """Test main post extraction on problematic shortcode"""
    
    shortcode = "C0xLaimIm1B"
    result = extract_main_post_only(shortcode)
    
    print("\\n" + "="*60)
    print("🎯 MAIN POST ONLY EXTRACTION RESULTS")
    print("="*60)
    print(f"Shortcode: {result['shortcode']}")
    print(f"Post Type: {result['post_type']}")
    print(f"Main images: {len(result['main_post_images'])}")
    print(f"Related images: {len(result['related_images'])}")
    print(f"Success: {result['success']}")
    
    if result['main_post_images']:
        print(f"\\n🖼️  MAIN POST IMAGES:")
        for i, img in enumerate(result['main_post_images'], 1):
            print(f"   {i}. {img['alt'][:60]}")
            print(f"      {img['src'][:80]}...")
            print(f"      Source: {img['source']}")
    
    if result['related_images']:
        print(f"\\n📋 RELATED IMAGES (excluded):")
        for i, img in enumerate(result['related_images'], 1):
            print(f"   {i}. {img['alt'][:60]}")
    
    if result.get('error'):
        print(f"\\n❌ Error: {result['error']}")

if __name__ == "__main__":
    test_main_post_extraction()