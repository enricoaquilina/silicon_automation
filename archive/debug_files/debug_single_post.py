#!/usr/bin/env python3
"""
Debug Single Post
Check if C0xLaimIm1B is actually a single post and where extra images come from
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_single_post():
    """Debug what type of post C0xLaimIm1B actually is"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # NOT headless so we can visually verify
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        shortcode = "C0xLaimIm1B"
        url = f"https://www.instagram.com/p/{shortcode}/"
        
        print(f"🔍 Manually checking: {url}")
        print("👀 Please visually verify:")
        print("   - Is this a single image post or carousel?")
        print("   - How many images do YOU see in the post?")
        print("   - Are there related posts below that might be causing confusion?")
        
        driver.get(url)
        time.sleep(8)
        
        # Check for carousel navigation buttons
        print(f"\n🔍 Looking for carousel indicators...")
        
        # Look for next/prev buttons
        try:
            next_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Next']")
            prev_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Previous']")
            
            print(f"   Next buttons found: {len(next_buttons)}")
            print(f"   Previous buttons found: {len(prev_buttons)}")
            
            if len(next_buttons) > 0 or len(prev_buttons) > 0:
                print("   🎠 CAROUSEL DETECTED - has navigation buttons")
            else:
                print("   📷 SINGLE POST - no navigation buttons")
                
        except Exception as e:
            print(f"   ❌ Button check failed: {e}")
        
        # Check all img elements and categorize them
        print(f"\n🔍 Analyzing all images on page...")
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        main_post_images = []
        profile_images = []
        related_images = []
        other_images = []
        
        for i, img in enumerate(img_elements):
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if "fbcdn.net" in src:
                if "t51.29350-15" in src:  # Content images
                    main_post_images.append({"index": i, "src": src[:80], "alt": alt[:50]})
                elif "t51.2885-19" in src:  # Profile images
                    profile_images.append({"index": i, "src": src[:80], "alt": alt[:50]})
                else:
                    other_images.append({"index": i, "src": src[:80], "alt": alt[:50]})
        
        print(f"\n📊 IMAGE BREAKDOWN:")
        print(f"   Content images (t51.29350-15): {len(main_post_images)}")
        print(f"   Profile images (t51.2885-19): {len(profile_images)}")
        print(f"   Other fbcdn images: {len(other_images)}")
        
        print(f"\n🖼️  CONTENT IMAGES DETAILS:")
        for img in main_post_images:
            print(f"   {img['index']}: {img['alt']}")
            print(f"      {img['src']}...")
        
        # Check page source for carousel data
        import re
        page_source = driver.page_source
        
        carousel_patterns = [
            r'"count":\s*(\d+)',
            r'carousel',
            r'sidecar'
        ]
        
        print(f"\n🔍 PAGE SOURCE ANALYSIS:")
        for pattern in carousel_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"   Found '{pattern}': {matches[:3]}")
            else:
                print(f"   Not found: '{pattern}'")
        
        print(f"\n💡 MANUAL VERIFICATION NEEDED:")
        print(f"   1. Look at the post - is it single image or carousel?")
        print(f"   2. Check if there are dots at bottom indicating multiple images")
        print(f"   3. Try swiping/clicking to see if there are more images")
        print(f"   4. Scroll down to see related posts (should be separate)")
        
        input("\\nPress Enter after manual verification...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_single_post()