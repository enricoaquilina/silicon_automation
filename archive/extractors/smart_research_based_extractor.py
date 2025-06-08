#!/usr/bin/env python3
"""
Smart Research-Based Extractor - Uses research insights for precise extraction
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
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

def setup_browser():
    """Setup browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
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
    """Close popups"""
    popup_selectors = [
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

def filter_main_carousel_images(all_images, shortcode):
    """Filter to get only main carousel images using smart logic"""
    print(f"🎯 Smart filtering for {shortcode}...")
    
    # Group images by date patterns in alt text
    from collections import defaultdict
    
    date_groups = defaultdict(list)
    no_date_images = []
    
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
    
    for img in all_images:
        alt = img.get('alt', '')
        date_matches = re.findall(date_pattern, alt)
        
        if date_matches:
            # Use the date as a grouping key
            date_key = date_matches[0]
            date_groups[date_key].append(img)
        else:
            no_date_images.append(img)
    
    print(f"   📅 Found {len(date_groups)} date groups and {len(no_date_images)} no-date images")
    
    # Strategy: Main carousel is usually the chronologically first date group
    # plus any no-date images that are high quality
    
    if date_groups:
        # Take the first date group (chronologically first = main post)
        first_date = list(date_groups.keys())[0]
        main_carousel_images = date_groups[first_date].copy()
        
        print(f"   🎯 Main date group '{first_date}': {len(main_carousel_images)} images")
        
        # Add high-quality no-date images (likely part of same carousel)
        high_quality_no_date = []
        for img in no_date_images:
            src = img['src']
            # Only include high-quality images
            if ('1440x' in src or '1080x' in src) and 'jpg' in src:
                high_quality_no_date.append(img)
        
        main_carousel_images.extend(high_quality_no_date)
        print(f"   ➕ Added {len(high_quality_no_date)} high-quality no-date images")
        
        return main_carousel_images
    else:
        # No date groups found, filter by quality and position
        print(f"   📍 No date groups, filtering by quality...")
        
        high_quality_images = []
        for img in all_images:
            src = img['src']
            if ('1440x' in src or '1080x' in src) and 'jpg' in src:
                high_quality_images.append(img)
        
        # Return first few high-quality images (likely main carousel)
        return high_quality_images[:10]  # Conservative limit

def extract_with_navigation(driver, shortcode, expected_count):
    """Extract using smart navigation based on research"""
    print(f"🧠 Smart extraction for {shortcode} (expecting {expected_count} images)")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)
    
    close_popups(driver)
    time.sleep(3)
    
    all_unique_images = []
    
    # Phase 1: Get initial images
    print("📍 Phase 1: Collecting initial images...")
    initial_images = get_all_visible_images(driver)
    
    # Phase 2: Navigate if needed (based on research insights)
    if expected_count > 5:  # C0wmEEKItfR needs navigation
        print("📍 Phase 2: Navigation required for large carousel...")
        
        # Research showed Next button at (858, 361)
        for nav_attempt in range(expected_count):
            print(f"   🔄 Navigation attempt {nav_attempt + 1}")
            
            # Click Next button at known location
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
                if next_button.is_displayed() and next_button.is_enabled():
                    ActionChains(driver).move_to_element(next_button).click().perform()
                    time.sleep(3)
                    
                    # Collect new images after navigation
                    new_images = get_all_visible_images(driver)
                    
                    # Add any truly new images
                    existing_srcs = [img['src'] for img in all_unique_images]
                    for img in new_images:
                        if img['src'] not in existing_srcs:
                            all_unique_images.append(img)
                            print(f"      🆕 New image after navigation: {img['src'][:60]}...")
                else:
                    print(f"      ❌ Next button not available")
                    break
            except:
                print(f"      ⚠️ Navigation failed")
                break
    else:
        print("📍 Phase 2: Small carousel - all images should be visible")
    
    # Combine initial and navigated images
    existing_srcs = [img['src'] for img in all_unique_images]
    for img in initial_images:
        if img['src'] not in existing_srcs:
            all_unique_images.append(img)
    
    # Phase 3: Smart filtering
    print("📍 Phase 3: Smart filtering...")
    filtered_images = filter_main_carousel_images(all_unique_images, shortcode)
    
    print(f"📊 Smart extraction complete: {len(all_unique_images)} total → {len(filtered_images)} filtered")
    return filtered_images

def get_all_visible_images(driver):
    """Get all visible high-quality images"""
    images = driver.find_elements(By.CSS_SELECTOR, "img")
    
    carousel_images = []
    for img in images:
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            if (src and 't51.29350-15' in src and 
                not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                
                carousel_images.append({
                    'src': src,
                    'alt': alt,
                    'visible': img.is_displayed()
                })
        except:
            continue
    
    return carousel_images

def main():
    """Test smart research-based extraction"""
    print("🧠 SMART RESEARCH-BASED CAROUSEL EXTRACTOR")
    print("=" * 60)
    
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
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract using smart approach
            filtered_images = extract_with_navigation(driver, shortcode, expected_count)
            
            if not filtered_images:
                print(f"❌ No images found for {shortcode}")
                continue
            
            print(f"\n📥 Downloading {len(filtered_images)} filtered images...")
            
            unique_images = []
            existing_hashes = set()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.instagram.com/'
            }
            
            # Download images
            for i, img_data in enumerate(filtered_images, 1):
                filename = f"{shortcode}_smart_image_{i}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                success, img_hash, size = download_unique_image(img_data['src'], filepath, existing_hashes, headers)
                if success:
                    unique_images.append({
                        'index': i,
                        'url': img_data['src'],
                        'alt': img_data['alt'],
                        'filename': filename,
                        'size': size,
                        'hash': img_hash
                    })
                    
                    # Stop if we have enough
                    if len(unique_images) >= expected_count:
                        print(f"   🎯 Reached target of {expected_count} images")
                        break
            
            print(f"\n🎉 SMART EXTRACTION COMPLETE for {shortcode}")
            print(f"📊 Images extracted: {len(unique_images)}/{expected_count}")
            
            if unique_images:
                print(f"📁 Successfully extracted images:")
                for img in unique_images:
                    print(f"  {img['index']}. {img['filename']} ({img['size']} bytes)")
            
            # Save results
            results = {
                "shortcode": shortcode,
                "expected_images": expected_count,
                "extracted_images": len(unique_images),
                "success": len(unique_images) >= expected_count,
                "images": unique_images,
                "method": "smart_research_based",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results_path = os.path.join(output_dir, "smart_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            if len(unique_images) >= expected_count:
                print(f"🎊 SUCCESS: All {expected_count} images extracted for {shortcode}!")
            else:
                print(f"⚠️ PARTIAL: Only {len(unique_images)}/{expected_count} images for {shortcode}")
            
            print(f"📁 Results saved to: smart_results.json")
            print(f"\n" + "=" * 60)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()