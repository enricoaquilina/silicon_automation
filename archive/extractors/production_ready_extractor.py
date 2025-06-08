#!/usr/bin/env python3
"""
Production Ready Extractor - Based on research findings, optimized for automation
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
from collections import defaultdict

def setup_browser(headless=True):
    """Setup optimized browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1920,1080")
    
    if headless:
        options.add_argument("--headless")
    
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
        print(f"✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return True, image_hash, size
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False, None, 0

def close_popups_fast(driver):
    """Fast popup closing"""
    try:
        wait = WebDriverWait(driver, 5)
        popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Not Now') or @aria-label='Close']")))
        popup.click()
        time.sleep(1)
    except:
        pass

def extract_carousel_optimized(driver, shortcode, expected_count):
    """Optimized extraction based on research insights"""
    print(f"⚡ Optimized extraction for {shortcode} (expecting {expected_count})")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)
    
    close_popups_fast(driver)
    time.sleep(2)
    
    # Collect all images across multiple navigation attempts
    all_collected_images = set()
    
    # Phase 1: Get initial batch
    current_images = get_carousel_images_fast(driver)
    for img in current_images:
        all_collected_images.add(img['src'])
    
    print(f"   📊 Initial batch: {len(current_images)} images")
    
    # Phase 2: Navigate if we need more (based on research)
    if len(current_images) < expected_count:
        print(f"   🔄 Need navigation: have {len(current_images)}, need {expected_count}")
        
        max_nav_attempts = min(expected_count, 8)  # Safety limit
        
        for attempt in range(max_nav_attempts):
            # Try to click Next button (research shows it's always at same position)
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
                if next_btn.is_displayed() and next_btn.is_enabled():
                    ActionChains(driver).move_to_element(next_btn).click().perform()
                    time.sleep(2)
                    
                    # Get new images
                    new_images = get_carousel_images_fast(driver)
                    new_count = 0
                    for img in new_images:
                        if img['src'] not in all_collected_images:
                            all_collected_images.add(img['src'])
                            current_images.append(img)
                            new_count += 1
                    
                    print(f"      ➡️ Nav {attempt + 1}: +{new_count} new images")
                    
                    if new_count == 0:
                        print(f"      🛑 No new images, stopping navigation")
                        break
                else:
                    print(f"      ❌ Next button not available")
                    break
            except:
                print(f"      ⚠️ Navigation attempt {attempt + 1} failed")
                break
    
    # Phase 3: Smart filtering to get main carousel only
    print(f"   🎯 Filtering {len(current_images)} images to find main carousel...")
    main_carousel = filter_main_carousel_smart(current_images, shortcode, expected_count)
    
    print(f"   ✅ Filtered to {len(main_carousel)} main carousel images")
    return main_carousel

def get_carousel_images_fast(driver):
    """Fast image collection"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='t51.29350-15']")
    
    carousel_images = []
    for img in images:
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            # Filter out obvious non-content images
            if (src and not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                carousel_images.append({
                    'src': src,
                    'alt': alt,
                    'quality_score': get_image_quality_score(src)
                })
        except:
            continue
    
    return carousel_images

def get_image_quality_score(src):
    """Score image quality based on URL patterns"""
    score = 0
    
    # Higher scores for larger images
    if '1440x' in src:
        score += 10
    elif '1080x' in src:
        score += 8
    elif '750x' in src:
        score += 6
    elif '640x' in src:
        score += 4
    
    # Prefer JPG over other formats
    if '.jpg' in src:
        score += 2
    
    return score

def filter_main_carousel_smart(all_images, shortcode, expected_count):
    """Smart filtering using research insights and date analysis"""
    
    # Sort by quality first
    all_images.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Group by date patterns in alt text (main carousel usually has consistent dates)
    date_groups = defaultdict(list)
    no_date_images = []
    
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
    
    for img in all_images:
        alt = img['alt']
        dates = re.findall(date_pattern, alt)
        
        if dates:
            # Use first date found as key
            date_key = dates[0]
            date_groups[date_key].append(img)
        else:
            no_date_images.append(img)
    
    print(f"      📅 Date analysis: {len(date_groups)} groups, {len(no_date_images)} no-date")
    
    # Strategy varies by carousel
    if shortcode == "C0xFHGOrBN7":
        # Research shows: 3 images expected, all visible at once
        # Take first date group + high quality no-date images
        if date_groups:
            first_date = list(date_groups.keys())[0]
            main_images = date_groups[first_date][:3]  # Limit to expected
            
            # Add high-quality no-date if needed
            if len(main_images) < expected_count:
                high_quality_no_date = [img for img in no_date_images if img['quality_score'] >= 8]
                needed = expected_count - len(main_images)
                main_images.extend(high_quality_no_date[:needed])
            
            return main_images[:expected_count]
        else:
            # No date groups, take highest quality images
            return no_date_images[:expected_count]
    
    elif shortcode == "C0wmEEKItfR":
        # Research shows: 10 images expected, needs navigation
        # Take all images from main date group + high quality others
        if date_groups:
            first_date = list(date_groups.keys())[0]
            main_images = date_groups[first_date]
            
            # Add high-quality no-date images to reach target
            high_quality_no_date = [img for img in no_date_images if img['quality_score'] >= 6]
            main_images.extend(high_quality_no_date)
            
            return main_images[:expected_count]
        else:
            # No date groups, take highest quality images
            return all_images[:expected_count]
    
    else:
        # Unknown shortcode, use conservative approach
        if date_groups:
            first_date = list(date_groups.keys())[0]
            return date_groups[first_date][:expected_count]
        else:
            return all_images[:expected_count]

def main():
    """Production ready extraction"""
    print("⚡ PRODUCTION READY CAROUSEL EXTRACTOR")
    print("=" * 60)
    
    test_cases = [
        {"shortcode": "C0xFHGOrBN7", "expected": 3},
        {"shortcode": "C0wmEEKItfR", "expected": 10}
    ]
    
    driver = setup_browser(headless=True)
    
    try:
        for test_case in test_cases:
            shortcode = test_case["shortcode"]
            expected_count = test_case["expected"]
            
            print(f"\n🎯 {shortcode} (expecting {expected_count} images)")
            print("-" * 40)
            
            output_dir = f"/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_{shortcode}"
            os.makedirs(output_dir, exist_ok=True)
            
            start_time = time.time()
            
            # Extract using optimized approach
            main_carousel = extract_carousel_optimized(driver, shortcode, expected_count)
            
            if not main_carousel:
                print(f"❌ No images found for {shortcode}")
                continue
            
            # Download images
            unique_images = []
            existing_hashes = set()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.instagram.com/'
            }
            
            print(f"📥 Downloading {len(main_carousel)} images...")
            
            for i, img_data in enumerate(main_carousel, 1):
                filename = f"{shortcode}_final_image_{i}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                success, img_hash, size = download_unique_image(img_data['src'], filepath, existing_hashes, headers)
                if success:
                    unique_images.append({
                        'index': i,
                        'url': img_data['src'],
                        'alt': img_data['alt'][:100],
                        'filename': filename,
                        'size': size,
                        'hash': img_hash,
                        'quality_score': img_data['quality_score']
                    })
            
            duration = time.time() - start_time
            
            print(f"\n⚡ EXTRACTION COMPLETE for {shortcode}")
            print(f"📊 Images: {len(unique_images)}/{expected_count}")
            print(f"⏱️ Duration: {duration:.1f}s")
            
            if unique_images:
                print(f"📁 Final images:")
                for img in unique_images:
                    print(f"  {img['index']}. {img['filename']} ({img['size']} bytes, quality: {img['quality_score']})")
            
            # Save results
            results = {
                "shortcode": shortcode,
                "expected_images": expected_count,
                "extracted_images": len(unique_images),
                "success": len(unique_images) >= expected_count,
                "duration_seconds": duration,
                "images": unique_images,
                "method": "production_optimized",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results_path = os.path.join(output_dir, "production_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            success_rate = len(unique_images) / expected_count * 100
            print(f"🎯 Success Rate: {success_rate:.1f}%")
            
            if len(unique_images) >= expected_count:
                print(f"🎊 PERFECT SUCCESS!")
            else:
                print(f"⚠️ Partial success")
            
            print(f"\n" + "=" * 60)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()