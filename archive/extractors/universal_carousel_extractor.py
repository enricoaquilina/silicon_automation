#!/usr/bin/env python3
"""
Universal Carousel Extractor - Extract all images from any Instagram carousel
Works for both C0xFHGOrBN7 (3 images) and C0wmEEKItfR (10 images)
"""

import os
import time
import hashlib
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

def setup_browser():
    """Setup browser with anti-detection"""
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

def get_image_hash(image_bytes):
    """Get hash of image content"""
    return hashlib.md5(image_bytes).hexdigest()

def download_unique_image(url: str, filepath: str, existing_hashes: set, headers: dict) -> tuple:
    """Download image only if it's unique"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        image_hash = get_image_hash(response.content)
        if image_hash in existing_hashes:
            return False, image_hash, 0
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        existing_hashes.add(image_hash)
        print(f"✅ Downloaded unique image: {os.path.basename(filepath)} ({size} bytes)")
        return True, image_hash, size
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False, None, 0

def close_popups(driver):
    """Close all popups"""
    popup_selectors = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow')]", 
        "//button[contains(text(), 'Not Now')]",
        "//button[@aria-label='Close']"
    ]
    
    for selector in popup_selectors:
        try:
            wait = WebDriverWait(driver, 3)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            element.click()
            time.sleep(1)
            break
        except:
            continue

def get_all_page_images(driver):
    """Get all high-quality content images from the page"""
    print("🔍 Scanning page for all high-quality images...")
    
    # Wait for page to fully load
    time.sleep(5)
    
    # Scroll to trigger loading of all content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    all_urls = set()
    
    # Method 1: Scan all img elements
    print("  📊 Method 1: Scanning img elements...")
    images = driver.find_elements(By.CSS_SELECTOR, "img")
    
    for img in images:
        src = img.get_attribute('src')
        if (src and 't51.29350-15' in src and 
            not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
            all_urls.add(src)
            print(f"    🖼️ Found: {src[:60]}...")
    
    # Method 2: Scan page source for URLs
    print("  📊 Method 2: Scanning page source...")
    page_source = driver.page_source
    
    # Find Instagram image URLs in page source
    patterns = [
        r'https://[^"\']*t51\.29350-15[^"\']*\.jpg[^"\']*',
        r'https://[^"\']*t51\.29350-15[^"\']*\.jpeg[^"\']*',
        r'https://[^"\']*scontent[^"\']*t51\.29350-15[^"\']*'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            # Clean URL
            clean_url = match.split('\\')[0].split('"')[0].split("'")[0]
            if (not any(ex in clean_url.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
                clean_url not in all_urls):
                all_urls.add(clean_url)
                print(f"    🔍 Found in source: {clean_url[:60]}...")
    
    # Method 3: Check srcset attributes
    print("  📊 Method 3: Scanning srcset attributes...")
    elements = driver.find_elements(By.CSS_SELECTOR, "[srcset]")
    
    for elem in elements:
        srcset = elem.get_attribute('srcset') or ''
        if 't51.29350-15' in srcset:
            urls = re.findall(r'https://[^\s,]+', srcset)
            for url in urls:
                if (not any(ex in url.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
                    url not in all_urls):
                    all_urls.add(url)
                    print(f"    🎭 Found in srcset: {url[:60]}...")
    
    print(f"  📊 Total unique URLs found: {len(all_urls)}")
    return list(all_urls)

def extract_carousel_comprehensive(driver, shortcode, output_dir, expected_count):
    """Extract all carousel images using comprehensive approach"""
    print(f"🎠 Starting comprehensive carousel extraction for {shortcode}")
    print(f"🎯 Expected images: {expected_count}")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)  # Longer wait for full page load
    
    close_popups(driver)
    time.sleep(3)
    
    unique_images = []
    existing_hashes = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Get all potential image URLs from the page
    all_urls = get_all_page_images(driver)
    
    if not all_urls:
        print("❌ No images found on page")
        return unique_images
    
    print(f"\n📥 Downloading all unique images...")
    
    # Download all unique images
    for i, url in enumerate(all_urls, 1):
        print(f"\n📍 Processing image {i}/{len(all_urls)}")
        
        # Test if URL is accessible
        try:
            head_response = requests.head(url, headers=headers, timeout=10)
            if head_response.status_code != 200:
                print(f"   ⚠️ URL not accessible: {head_response.status_code}")
                continue
        except Exception as e:
            print(f"   ⚠️ URL check failed: {e}")
            continue
        
        filename = f"{shortcode}_image_{len(unique_images) + 1}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        success, img_hash, size = download_unique_image(url, filepath, existing_hashes, headers)
        if success:
            unique_images.append({
                'index': len(unique_images),
                'url': url,
                'filename': filename,
                'size': size,
                'hash': img_hash
            })
            print(f"   📸 Saved as image #{len(unique_images)}")
            
            # Stop if we've reached the expected count
            if len(unique_images) >= expected_count:
                print(f"   🎯 Reached target of {expected_count} images")
                break
        else:
            print(f"   🔄 Skipped duplicate or failed")
    
    return unique_images

def main():
    """Extract carousel images for specified shortcode"""
    print("🎯 UNIVERSAL CAROUSEL EXTRACTOR")
    print("=" * 60)
    
    # Test both shortcodes
    test_cases = [
        {"shortcode": "C0xFHGOrBN7", "expected": 3},
        {"shortcode": "C0wmEEKItfR", "expected": 10}
    ]
    
    driver = setup_browser()
    
    try:
        for test_case in test_cases:
            shortcode = test_case["shortcode"]
            expected_count = test_case["expected"]
            
            print(f"\n🔄 Testing {shortcode} (expecting {expected_count} images)")
            print("-" * 40)
            
            output_dir = f"/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_{shortcode}"
            
            # Clear existing files
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.endswith(('.jpg', '.png', '.jpeg')):
                        os.remove(os.path.join(output_dir, file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract images
            unique_images = extract_carousel_comprehensive(driver, shortcode, output_dir, expected_count)
            
            print(f"\n🎉 EXTRACTION COMPLETE for {shortcode}")
            print(f"📊 Images extracted: {len(unique_images)}/{expected_count}")
            
            if unique_images:
                print(f"📁 Successfully extracted images:")
                for img in unique_images:
                    print(f"  {img['index'] + 1}. {img['filename']} ({img['size']} bytes)")
            
            # Save extraction info
            extraction_info = {
                "shortcode": shortcode,
                "expected_images": expected_count,
                "extracted_images": len(unique_images),
                "success": len(unique_images) >= expected_count,
                "images": unique_images,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            info_path = os.path.join(output_dir, "extraction_info.json")
            with open(info_path, 'w') as f:
                json.dump(extraction_info, f, indent=2)
            
            # Status
            if len(unique_images) >= expected_count:
                print(f"🎊 SUCCESS: All {expected_count} images extracted for {shortcode}!")
            else:
                print(f"⚠️ PARTIAL: Only {len(unique_images)}/{expected_count} images for {shortcode}")
            
            print(f"\n" + "=" * 60)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()