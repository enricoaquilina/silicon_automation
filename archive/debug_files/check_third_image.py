#!/usr/bin/env python3
"""
Check if there's actually a third carousel image by navigating to img_index=3
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def main():
    driver = setup_browser()
    
    try:
        # Navigate to the third image
        url = "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=3"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Find all images
        images = driver.find_elements(By.CSS_SELECTOR, "img")
        print(f"📊 Found {len(images)} total images")
        
        # Look for main content images
        main_images = []
        for img in images:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if "fbcdn.net" in src and "t51.29350-15" in src:
                main_images.append({
                    "src": src,
                    "alt": alt
                })
                print(f"   Image: {src[:80]}...")
                print(f"   Alt: {alt}")
                print()
        
        print(f"✅ Found {len(main_images)} main content images")
        
        # Check page title or any indicators
        title = driver.title
        print(f"Page title: {title}")
        
        # Check if there are carousel navigation indicators
        nav_elements = driver.find_elements(By.CSS_SELECTOR, "[role='button'][aria-label*='Next'], [role='button'][aria-label*='Previous']")
        if nav_elements:
            print(f"🎠 Found {len(nav_elements)} carousel navigation elements")
        
        input("Press Enter to close browser and continue...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()