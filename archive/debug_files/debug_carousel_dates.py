#!/usr/bin/env python3
"""
Debug Carousel Dates
See exactly what date groups we're getting for the carousel
"""

import time
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_carousel_dates(shortcode: str):
    """Debug the date filtering logic"""
    
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
        print(f"🔍 Debug carousel dates: {url}")
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
        
        # Get img elements with "Photo by"
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        main_post_images = []
        for img in img_elements:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if (src and "fbcdn.net" in src and 
                "t51.29350-15" in src and
                not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar']) and
                "Photo by" in alt):
                
                main_post_images.append({
                    "src": src,
                    "alt": alt
                })
        
        print(f"📊 Found {len(main_post_images)} post content images")
        
        # Apply date filtering logic
        date_groups = defaultdict(list)
        
        for i, img_data in enumerate(main_post_images):
            alt = img_data["alt"]
            print(f"\\n{i+1}. Alt: {alt}")
            
            # Extract date from alt text
            date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data["src"])
                print(f"   📅 Date: {date}")
            else:
                print(f"   ❌ No date found")
            
            print(f"   🖼️  URL: {img_data['src'][:60]}...")
        
        print(f"\\n📋 DATE GROUPS:")
        for date, urls in date_groups.items():
            print(f"   📅 {date}: {len(urls)} images")
            for i, url in enumerate(urls, 1):
                print(f"      {i}. {url[:60]}...")
        
        if date_groups:
            main_date = max(date_groups.keys(), key=lambda k: len(date_groups[k]))
            main_post_urls = date_groups[main_date]
            print(f"\\n✅ SELECTED:")
            print(f"   📅 Main date: {main_date}")
            print(f"   🖼️  Images: {len(main_post_urls)}")
            
            # Check if we're missing any images that should be included
            print(f"\\n💡 ANALYSIS:")
            if len(main_post_urls) < 3:
                print(f"   ⚠️ Expected 3 images, got {len(main_post_urls)}")
                print(f"   📝 Possible issues:")
                print(f"      - 3rd image might have different date in alt text")
                print(f"      - 3rd image might not have 'Photo by' in alt")
                print(f"      - 3rd image might be filtered out by other criteria")
                
                # Show images without "Photo by"
                other_images = []
                for img in img_elements:
                    src = img.get_attribute("src") or ""
                    alt = img.get_attribute("alt") or ""
                    
                    if (src and "fbcdn.net" in src and 
                        "t51.29350-15" in src and
                        not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar']) and
                        "Photo by" not in alt):
                        
                        other_images.append({"src": src, "alt": alt})
                
                if other_images:
                    print(f"   🔍 Images without 'Photo by': {len(other_images)}")
                    for i, img in enumerate(other_images, 1):
                        print(f"      {i}. {img['alt'][:50]}...")
            else:
                print(f"   ✅ Found expected number of images!")
        else:
            print(f"\\n❌ No date groups found!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_carousel_dates("C0xFHGOrBN7")