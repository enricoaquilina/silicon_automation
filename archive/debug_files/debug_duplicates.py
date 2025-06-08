#!/usr/bin/env python3
"""
Debug Duplicates
Analyze exactly what images we're getting and why there are duplicates
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_duplicates(shortcode: str):
    """Debug what images we're getting and identify duplicates"""
    
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
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Debug duplicates: {url}")
        driver.get(url)
        
        # Handle cookie popup
        try:
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
            )
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        # Wait for dynamic loading
        time.sleep(10)
        
        # Check carousel detection
        carousel_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "button[aria-label*='Next'], button[aria-label*='Previous'], [aria-label*='Go to']")
        
        is_carousel = len(carousel_buttons) > 0
        print(f"🎠 Carousel detected: {is_carousel} ({len(carousel_buttons)} nav buttons)")
        
        # Get all img elements
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        print(f"📊 Total img elements: {len(img_elements)}")
        
        # Categorize all images
        content_images = []
        profile_images = []
        other_images = []
        
        for i, img in enumerate(img_elements):
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if "fbcdn.net" in src:
                if "t51.29350-15" in src:  # Content images
                    content_images.append({
                        "index": i,
                        "src": src,
                        "alt": alt,
                        "has_photo_by": "Photo by" in alt
                    })
                elif "t51.2885-19" in src:  # Profile images
                    profile_images.append({
                        "index": i,
                        "src": src,
                        "alt": alt
                    })
                else:
                    other_images.append({
                        "index": i,
                        "src": src,
                        "alt": alt
                    })
        
        print(f"\\n📋 IMAGE BREAKDOWN:")
        print(f"   Content images (t51.29350-15): {len(content_images)}")
        print(f"   Profile images (t51.2885-19): {len(profile_images)}")
        print(f"   Other fbcdn images: {len(other_images)}")
        
        print(f"\\n🖼️  CONTENT IMAGES ANALYSIS:")
        for i, img in enumerate(content_images):
            print(f"   {i+1}. Index {img['index']}: Photo by: {img['has_photo_by']}")
            print(f"      Alt: {img['alt'][:80]}...")
            print(f"      URL: {img['src'][:80]}...")
            
            # Check for URL patterns that might indicate duplicates
            if "p1080x1080" in img['src']:
                print(f"      📐 High-res (1080x1080)")
            elif "p640x640" in img['src']:
                print(f"      📐 Medium-res (640x640)")
            else:
                print(f"      📐 Other resolution")
            print()
        
        # Filter for actual post content (has "Photo by")
        post_content_images = [img for img in content_images if img['has_photo_by']]
        print(f"📸 Post content images (with 'Photo by'): {len(post_content_images)}")
        
        # Analyze for uniqueness
        print(f"\\n🔍 UNIQUENESS ANALYSIS:")
        unique_by_alt = {}
        unique_by_url = {}
        
        for img in post_content_images:
            # Group by alt text patterns
            alt_key = img['alt'].split(" on ")[0] if " on " in img['alt'] else img['alt']
            if alt_key not in unique_by_alt:
                unique_by_alt[alt_key] = []
            unique_by_alt[alt_key].append(img)
            
            # Group by URL (different resolutions of same image)
            url_key = img['src'].split('?')[0].split('/')[-1].split('_')[0] if '_' in img['src'] else img['src']
            if url_key not in unique_by_url:
                unique_by_url[url_key] = []
            unique_by_url[url_key].append(img)
        
        print(f"   Unique by alt text: {len(unique_by_alt)} groups")
        for key, imgs in unique_by_alt.items():
            print(f"      '{key[:50]}...': {len(imgs)} images")
        
        print(f"   Unique by URL pattern: {len(unique_by_url)} groups")
        for key, imgs in unique_by_url.items():
            print(f"      '{key[:20]}...': {len(imgs)} images")
        
        # Recommend best deduplication strategy
        print(f"\\n💡 DEDUPLICATION RECOMMENDATIONS:")
        
        if is_carousel:
            expected_count = 3  # Based on your feedback
            
            if len(unique_by_url) == expected_count:
                print(f"   ✅ URL-based deduplication gives exactly {expected_count} images!")
                print(f"   📝 Strategy: Group by URL pattern, take highest resolution from each")
            elif len(unique_by_alt) == expected_count:
                print(f"   ✅ Alt-text deduplication gives exactly {expected_count} images!")
                print(f"   📝 Strategy: Group by alt text, take first from each")
            else:
                print(f"   ⚠️ Neither strategy gives exactly {expected_count} images")
                print(f"   📝 URL groups: {len(unique_by_url)}, Alt groups: {len(unique_by_alt)}")
                print(f"   📝 May need to take first {expected_count} from best strategy")
        else:
            print(f"   📷 Single post: Take first post content image")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test on the known 3-image carousel
    debug_duplicates("C0xFHGOrBN7")