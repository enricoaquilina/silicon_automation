#!/usr/bin/env python3
"""
Debug what images are actually present on the Instagram page
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def debug_images():
    driver = setup_browser()
    
    try:
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(10)
        
        print(f"📄 Page title: {driver.title}")
        print(f"📄 Current URL: {driver.current_url}")
        
        # Find ALL images
        all_images = driver.find_elements(By.TAG_NAME, "img")
        print(f"\n📊 Total images found: {len(all_images)}")
        
        for i, img in enumerate(all_images[:10]):  # Show first 10
            src = img.get_attribute('src')
            alt = img.get_attribute('alt')
            print(f"  {i+1}. src: {src[:80]}...")
            print(f"      alt: {alt}")
            print(f"      visible: {img.is_displayed()}")
            print()
        
        # Try different selectors
        selectors = [
            "img[src*='instagram']",
            "img[src*='cdninstagram']", 
            "img[src*='fbcdn']",
            "img[src*='scontent']",
            "article img",
            "img"
        ]
        
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"🔍 Selector '{selector}': {len(elements)} images")
            
            if elements:
                for i, img in enumerate(elements[:3]):
                    src = img.get_attribute('src')
                    if src:
                        print(f"    {i+1}. {src[:60]}...")
        
        # Check if page needs login
        login_indicators = driver.find_elements(By.CSS_SELECTOR, "a[href*='login'], button[type='submit']")
        if login_indicators:
            print("\n⚠️ Login required detected")
        
        # Save page source for analysis
        with open("debug_page_source.html", "w") as f:
            f.write(driver.page_source)
        print("\n💾 Page source saved to debug_page_source.html")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_images()