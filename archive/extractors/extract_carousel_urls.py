#!/usr/bin/env python3
"""
Extract carousel URLs using the fixed carousel extractor approach
"""

import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser with stealth configuration"""
    options = Options()
    options.add_argument('--headless')  # Run headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_carousel_urls(shortcode):
    """Extract carousel URLs from page source"""
    driver = setup_browser()
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Get page source
        page_source = driver.page_source
        
        # Find carousel_media pattern in page source
        carousel_pattern = r'"carousel_media":\s*\[(.*?)\]'
        carousel_match = re.search(carousel_pattern, page_source, re.DOTALL)
        
        if not carousel_match:
            print("❌ No carousel_media found in page source")
            return []
        
        carousel_data = carousel_match.group(1)
        
        # Extract image URLs with proper quality
        url_pattern = r'"url":\s*"([^"]*(?:1440x|1080x|640x)[^"]*\.jpg[^"]*)"'
        urls = re.findall(url_pattern, carousel_data)
        
        # Clean up URLs (remove escape characters)
        cleaned_urls = []
        for url in urls:
            cleaned_url = url.replace('\\/', '/').replace('\\u0026', '&')
            cleaned_urls.append(cleaned_url)
        
        print(f"✅ Found {len(cleaned_urls)} carousel images")
        return cleaned_urls
        
    finally:
        driver.quit()

def main():
    shortcode = "C0xFHGOrBN7"
    urls = extract_carousel_urls(shortcode)
    
    print(f"\\n📊 Extracted {len(urls)} carousel URLs:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    # Save to file
    with open("carousel_urls.txt", "w") as f:
        for i, url in enumerate(urls, 1):
            f.write(f"{i}. {url}\\n")
    
    print(f"\\n💾 URLs saved to carousel_urls.txt")

if __name__ == "__main__":
    main()