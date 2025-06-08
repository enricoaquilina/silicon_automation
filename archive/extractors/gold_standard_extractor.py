#!/usr/bin/env python3
"""
Gold Standard Extractor - Extract exact URLs and compare with gold standard
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

def get_image_hash(filepath):
    """Get hash of image file"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def download_image(url: str, filepath: str, headers: dict) -> bool:
    """Download image with proper headers"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

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

def extract_carousel_urls_from_source(driver, shortcode):
    """Extract carousel URLs directly from page source"""
    print(f"🔍 Extracting carousel URLs for {shortcode} from page source")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)
    
    close_popups(driver)
    time.sleep(3)
    
    # Get page source
    page_source = driver.page_source
    
    # Look specifically for the carousel URLs pattern
    carousel_pattern = r'https://[^"\']*t51\.29350-15[^"\']*\.jpg[^"\']*'
    
    found_urls = []
    matches = re.findall(carousel_pattern, page_source)
    
    print(f"📊 Found {len(matches)} potential URLs in page source")
    
    # Process and deduplicate URLs
    unique_urls = set()
    for match in matches:
        # Clean URL (remove potential escaping)
        clean_url = match.split('\\')[0].split('"')[0].split("'")[0]
        
        # Filter for main content images (not profile pics or thumbnails)
        if (not any(ex in clean_url.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
            'CAROUSEL_ITEM' in clean_url):  # Look for carousel-specific URLs
            unique_urls.add(clean_url)
            print(f"🎯 Carousel URL found: {clean_url[:100]}...")
    
    # Convert back to list and sort for consistency
    carousel_urls = sorted(list(unique_urls))
    
    print(f"📊 Final carousel URLs: {len(carousel_urls)}")
    return carousel_urls

def compare_with_gold_standard(extracted_urls, gold_dir):
    """Compare extracted images with gold standard"""
    print(f"\n🏆 Comparing with gold standard images...")
    
    # Get gold standard hashes
    gold_hashes = {}
    gold_files = ['gold1.jpg', 'gold2.jpg', 'gold3.jpg']
    
    for gold_file in gold_files:
        gold_path = os.path.join(gold_dir, gold_file)
        if os.path.exists(gold_path):
            gold_hash = get_image_hash(gold_path)
            if gold_hash:
                gold_hashes[gold_file] = gold_hash
                print(f"📋 Gold {gold_file}: {gold_hash[:12]}...")
    
    # Compare extracted images
    matches = []
    for i, url in enumerate(extracted_urls, 1):
        extracted_path = os.path.join(gold_dir, f"extracted_{i}.jpg")
        if os.path.exists(extracted_path):
            extracted_hash = get_image_hash(extracted_path)
            
            # Check if this hash matches any gold standard
            for gold_file, gold_hash in gold_hashes.items():
                if extracted_hash == gold_hash:
                    matches.append({
                        'extracted_index': i,
                        'gold_file': gold_file,
                        'hash': extracted_hash,
                        'url': url
                    })
                    print(f"✅ Match: extracted_{i}.jpg = {gold_file}")
                    break
            else:
                print(f"❌ No match: extracted_{i}.jpg ({extracted_hash[:12]}...)")
    
    return matches, gold_hashes

def main():
    """Extract carousel URLs and compare with gold standard"""
    print("🏆 GOLD STANDARD CAROUSEL EXTRACTION")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Gold standard URLs that we know are correct
    gold_urls = [
        "https://instagram.fmla1-2.fna.fbcdn.net/v/t51.29350-15/409688197_950875209793155_6981069157937748850_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0MTF4MTc2NC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-2.fna.fbcdn.net&_nc_cat=103&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=nKihT-cvaB0Q7kNvwFaPmKo&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3ODk3NjY3NTI1Nw%3D%3D.3-ccb7-5&oh=00_AfLzIk4I6XDgLn5XcYZ9y9xsXIxpy2pH3JZ-4Iws2C_NFg&oe=684601F4&_nc_sid=10d13b",
        "https://instagram.fmla1-1.fna.fbcdn.net/v/t51.29350-15/410140938_884927459607866_2818375595357090150_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-1.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=JACK5MYpcWwQ7kNvwFn5oRf&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3ODk1OTgxNDM1Mw%3D%3D.3-ccb7-5&oh=00_AfJ-9OJMvbAW_5CVGUO9y2Sw3cx7lIieC9UnkTL8MHWp5w&oe=684625CF&_nc_sid=10d13b",
        "https://instagram.fmla1-1.fna.fbcdn.net/v/t51.29350-15/410057185_1320618825266899_8930879645133735611_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-1.fna.fbcdn.net&_nc_cat=107&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=VnWDnJY6IQ0Q7kNvwGDRZlH&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3OTAxMDEwMDEzMA%3D%3D.3-ccb7-5&oh=00_AfIGsEav-ANocS2QStv-gmDWQKyCFzqcywmfbNebcsssjA&oe=68460C28&_nc_sid=10d13b"
    ]
    
    driver = setup_browser()
    
    try:
        # Extract carousel URLs from page source
        extracted_urls = extract_carousel_urls_from_source(driver, shortcode)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/'
        }
        
        print(f"\n📥 Downloading extracted images...")
        
        # Download extracted images
        for i, url in enumerate(extracted_urls[:3], 1):  # Limit to 3 as we know there are 3
            filename = f"extracted_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            download_image(url, filepath, headers)
        
        # Compare with gold standard
        matches, gold_hashes = compare_with_gold_standard(extracted_urls, output_dir)
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"Gold standard images: {len(gold_hashes)}")
        print(f"Extracted URLs: {len(extracted_urls)}")
        print(f"Perfect matches: {len(matches)}")
        
        if len(matches) == 3:
            print(f"🎊 PERFECT SUCCESS: All 3 carousel images extracted correctly!")
        else:
            print(f"⚠️ PARTIAL: {len(matches)}/3 images match gold standard")
        
        # Save detailed results
        results = {
            "shortcode": shortcode,
            "gold_urls": gold_urls,
            "extracted_urls": extracted_urls,
            "matches": matches,
            "success": len(matches) == 3,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        results_path = os.path.join(output_dir, "gold_standard_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📁 Results saved to: gold_standard_results.json")
        
        # Show which URLs we found vs what we expected
        print(f"\n🔍 URL COMPARISON:")
        print(f"Expected URLs:")
        for i, url in enumerate(gold_urls, 1):
            print(f"  {i}. {url[:100]}...")
        
        print(f"\nExtracted URLs:")
        for i, url in enumerate(extracted_urls, 1):
            print(f"  {i}. {url[:100]}...")
        
        return len(matches) == 3
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()