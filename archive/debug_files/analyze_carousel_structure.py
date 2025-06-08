#!/usr/bin/env python3
"""
Analyze the actual carousel structure to determine if there are 2 or 3 images
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def main():
    driver = setup_browser()
    
    try:
        # Navigate to the main post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        page_source = driver.page_source
        
        # Look for carousel_media in the page source
        print("\\n📊 Analyzing carousel structure...")
        
        # Find carousel_media JSON
        carousel_pattern = r'"carousel_media":\s*\[(.*?)\]'
        carousel_match = re.search(carousel_pattern, page_source, re.DOTALL)
        
        if carousel_match:
            carousel_data = carousel_match.group(1)
            print("✅ Found carousel_media in page source")
            
            # Count display_url entries
            display_urls = re.findall(r'"display_url":\s*"([^"]+)"', carousel_data)
            print(f"📊 Found {len(display_urls)} display_url entries")
            
            # Count id entries (unique images)
            image_ids = re.findall(r'"id":\s*"([^"]+)"', carousel_data)
            print(f"📊 Found {len(image_ids)} image ID entries")
            
            # Look for media_type entries
            media_types = re.findall(r'"media_type":\s*([0-9]+)', carousel_data)
            print(f"📊 Found {len(media_types)} media_type entries")
            
            # Count how many are photos (media_type: 1) vs videos (media_type: 2)
            photo_count = media_types.count('1')
            video_count = media_types.count('2')
            print(f"📸 Photos: {photo_count}, Videos: {video_count}")
            
            # Extract the actual URLs and analyze them
            print("\\n🖼️  Carousel images:")
            for i, url in enumerate(display_urls, 1):
                clean_url = url.replace("\\u0026", "&").replace("\\/", "/")
                
                # Extract image ID from URL
                image_id_match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', clean_url)
                if image_id_match:
                    image_id = image_id_match.group(1)
                    print(f"   {i}. ID: {image_id} - {clean_url[:80]}...")
                else:
                    print(f"   {i}. {clean_url[:80]}...")
            
        else:
            print("❌ No carousel_media found in page source")
            
        # Also look for edge_sidecar_to_children (another carousel indicator)
        sidecar_pattern = r'"edge_sidecar_to_children":\s*\{[^}]*"edges":\s*\[([^\]]+)\]'
        sidecar_match = re.search(sidecar_pattern, page_source)
        
        if sidecar_match:
            print("\\n✅ Found edge_sidecar_to_children structure")
            sidecar_data = sidecar_match.group(1)
            
            # Count nodes in sidecar
            node_count = len(re.findall(r'"node":\s*\{', sidecar_data))
            print(f"📊 Sidecar has {node_count} nodes")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()