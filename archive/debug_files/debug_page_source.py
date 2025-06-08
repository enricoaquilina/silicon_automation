#!/usr/bin/env python3
"""
Debug Page Source
Save page source and manually find the correct GraphQL patterns
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_page_source(shortcode: str):
    """Debug page source to find correct patterns"""
    
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
        print(f"🔍 Debugging: {url}")
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
        
        time.sleep(8)  # Wait for full load
        
        page_source = driver.page_source
        
        # Save full page source
        filename = f"page_source_{shortcode}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        print(f"📄 Saved page source to: {filename}")
        
        # Search for key patterns
        patterns_to_find = [
            "edge_sidecar_to_children",
            "GraphSidecar",
            "GraphImage", 
            "display_url",
            "shortcode_media",
            "__typename",
            "carousel",
            "sidecar"
        ]
        
        print(f"\\n🔍 Searching for key patterns:")
        for pattern in patterns_to_find:
            matches = len(re.findall(pattern, page_source, re.IGNORECASE))
            status = "✅" if matches > 0 else "❌"
            print(f"   {status} {pattern}: {matches} occurrences")
        
        # Look for JSON-like structures
        print(f"\\n🔍 Looking for JSON structures:")
        
        # Find all display_url occurrences
        display_urls = re.findall(r'"display_url":\s*"([^"]+)"', page_source)
        print(f"   📸 Found {len(display_urls)} display_url entries")
        
        if display_urls:
            print(f"   First few URLs:")
            for i, url in enumerate(display_urls[:3]):
                clean_url = url.replace('\\u0026', '&').replace('\\/', '/')
                print(f"      {i+1}: {clean_url[:60]}...")
        
        # Look for edge_sidecar_to_children structure
        sidecar_pattern = r'"edge_sidecar_to_children"[^}]*"edges"[^\\]]*\\[([^\\]]*)\\\]'
        sidecar_matches = re.findall(sidecar_pattern, page_source)
        print(f"   🎠 Found {len(sidecar_matches)} sidecar structures")
        
        # Look for script tags with JSON data
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', page_source, re.DOTALL)
        json_scripts = 0
        for script in script_tags:
            if any(key in script for key in ["display_url", "GraphSidecar", "edge_sidecar"]):
                json_scripts += 1
        
        print(f"   📜 Found {json_scripts} script tags with relevant JSON data")
        
        print(f"\\n💡 Next steps:")
        print(f"   1. Open {filename} in text editor")
        print(f"   2. Search for 'edge_sidecar_to_children' to find carousel data")
        print(f"   3. Search for 'display_url' to find image URLs")
        print(f"   4. Look at the JSON structure around these patterns")
        
    finally:
        driver.quit()

def test_debug():
    """Test debug on a known carousel"""
    # Test on known 3-image carousel
    debug_page_source("C0xFHGOrBN7")

if __name__ == "__main__":
    test_debug()