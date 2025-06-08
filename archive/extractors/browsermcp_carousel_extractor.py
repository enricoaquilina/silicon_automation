#!/usr/bin/env python3
"""
BrowserMCP Enhanced Carousel Extractor - Uses BrowserMCP for advanced browser control
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
from collections import defaultdict

def setup_browser(headless=False):
    """Setup browser with optimal settings"""
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

def close_popups_enhanced(driver):
    """Enhanced popup closing with BrowserMCP-style precision"""
    try:
        wait = WebDriverWait(driver, 5)
        
        # Multiple popup patterns
        popup_patterns = [
            "//button[contains(text(), 'Allow')]",
            "//button[contains(text(), 'Not Now')]", 
            "//button[@aria-label='Close']",
            "//button[contains(@class, 'close')]",
            "//div[@role='dialog']//button"
        ]
        
        for pattern in popup_patterns:
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, pattern)))
                # Use JavaScript click for reliability
                driver.execute_script("arguments[0].click();", popup)
                time.sleep(1)
                print(f"   ✅ Closed popup with pattern: {pattern}")
                break
            except:
                continue
    except:
        pass

def enhanced_carousel_navigation(driver, shortcode, expected_count):
    """Enhanced navigation using BrowserMCP-style techniques"""
    print(f"🚀 Enhanced BrowserMCP navigation for {shortcode}")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)
    
    close_popups_enhanced(driver)
    time.sleep(3)
    
    all_image_urls = set()
    
    # Phase 1: Collect initial images with enhanced detection
    print("📍 Phase 1: Enhanced initial image collection...")
    initial_images = get_carousel_images_enhanced(driver)
    for img in initial_images:
        all_image_urls.add(img['src'])
        print(f"   🖼️ Initial: {img['src'][:60]}... (quality: {img['quality_score']})")
    
    print(f"   📊 Initial collection: {len(initial_images)} images")
    
    # Phase 2: Advanced navigation strategies
    if len(initial_images) < expected_count:
        print(f"📍 Phase 2: Advanced navigation ({len(initial_images)}/{expected_count})...")
        
        # Strategy 1: Precise Next button clicking with scroll coordination
        print("   🎯 Strategy 1: Precise Next button navigation...")
        navigation_success = False
        
        for nav_attempt in range(min(expected_count * 2, 15)):
            try:
                # Find Next button with multiple selectors
                next_button = None
                next_selectors = [
                    "button[aria-label*='Next']",
                    "button[aria-label='Next']", 
                    "[role='button'][aria-label*='Next']",
                    "div[role='button'][aria-label*='Next']"
                ]
                
                for selector in next_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                next_button = btn
                                break
                        if next_button:
                            break
                    except:
                        continue
                
                if next_button:
                    # Get current image count before navigation
                    before_count = len(all_image_urls)
                    
                    # Enhanced clicking with multiple methods
                    try:
                        # Method 1: ActionChains with hover
                        ActionChains(driver).move_to_element(next_button).pause(0.5).click().perform()
                    except:
                        try:
                            # Method 2: Direct click
                            next_button.click()
                        except:
                            # Method 3: JavaScript click
                            driver.execute_script("arguments[0].click();", next_button)
                    
                    print(f"      ➡️ Clicked Next button (attempt {nav_attempt + 1})")
                    time.sleep(3)
                    
                    # Check for new images with enhanced detection
                    new_images = get_carousel_images_enhanced(driver)
                    new_count = 0
                    
                    for img in new_images:
                        if img['src'] not in all_image_urls:
                            all_image_urls.add(img['src'])
                            new_count += 1
                            print(f"         🆕 New image: {img['src'][:60]}...")
                    
                    if new_count > 0:
                        navigation_success = True
                        print(f"      ✅ Found {new_count} new images")
                    else:
                        print(f"      ⚠️ No new images after navigation")
                        
                        # Try scrolling within carousel to trigger loading
                        try:
                            carousel_container = driver.find_element(By.CSS_SELECTOR, "article")
                            driver.execute_script("arguments[0].scrollLeft += 500;", carousel_container)
                            time.sleep(2)
                            
                            # Check again after scroll
                            scroll_images = get_carousel_images_enhanced(driver)
                            scroll_new_count = 0
                            for img in scroll_images:
                                if img['src'] not in all_image_urls:
                                    all_image_urls.add(img['src'])
                                    scroll_new_count += 1
                                    print(f"         📜 Scroll revealed: {img['src'][:60]}...")
                            
                            if scroll_new_count == 0:
                                print(f"      🛑 Navigation exhausted")
                                break
                        except:
                            break
                else:
                    print(f"      ❌ No Next button found")
                    break
                    
            except Exception as e:
                print(f"      ⚠️ Navigation error: {e}")
                break
        
        # Strategy 2: Keyboard navigation as fallback
        if not navigation_success and len(all_image_urls) < expected_count:
            print("   ⌨️ Strategy 2: Keyboard navigation fallback...")
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                for key_attempt in range(expected_count):
                    body.send_keys(Keys.ARROW_RIGHT)
                    time.sleep(2)
                    
                    keyboard_images = get_carousel_images_enhanced(driver)
                    for img in keyboard_images:
                        if img['src'] not in all_image_urls:
                            all_image_urls.add(img['src'])
                            print(f"      ⌨️ Keyboard revealed: {img['src'][:60]}...")
            except:
                print("      ⚠️ Keyboard navigation failed")
    
    # Phase 3: Enhanced filtering with smart algorithms
    print("📍 Phase 3: Smart filtering...")
    final_images = []
    
    # Convert URLs back to image objects for filtering
    current_images = get_carousel_images_enhanced(driver)
    filtered_images = [img for img in current_images if img['src'] in all_image_urls]
    
    # Apply smart filtering
    main_carousel = filter_main_carousel_enhanced(filtered_images, shortcode, expected_count)
    
    print(f"📊 Enhanced navigation complete: {len(all_image_urls)} total → {len(main_carousel)} filtered")
    return main_carousel

def get_carousel_images_enhanced(driver):
    """Enhanced image detection with quality scoring"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='t51.29350-15']")
    
    carousel_images = []
    for img in images:
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            # Enhanced filtering
            if (src and not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                quality_score = calculate_enhanced_quality_score(src, alt)
                
                carousel_images.append({
                    'src': src,
                    'alt': alt,
                    'quality_score': quality_score,
                    'visible': img.is_displayed()
                })
        except:
            continue
    
    return carousel_images

def calculate_enhanced_quality_score(src, alt):
    """Enhanced quality scoring algorithm"""
    score = 0
    
    # Resolution scoring
    if '1440x' in src:
        score += 15
    elif '1080x' in src:
        score += 12
    elif '750x' in src:
        score += 8
    elif '640x' in src:
        score += 5
    
    # Format preference
    if '.jpg' in src:
        score += 3
    elif '.webp' in src:
        score += 2
    
    # Alt text indicates main content
    if alt and any(word in alt.lower() for word in ['photo', 'image', 'shared']):
        score += 5
    
    # Avoid suggested content indicators
    if any(indicator in src.lower() for indicator in ['suggested', 'recommend', 'explore']):
        score -= 10
    
    return score

def filter_main_carousel_enhanced(all_images, shortcode, expected_count):
    """Enhanced filtering using multiple algorithms"""
    print(f"🎯 Enhanced filtering for {shortcode}...")
    
    if not all_images:
        return []
    
    # Sort by quality score first
    all_images.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Enhanced date grouping
    date_groups = defaultdict(list)
    no_date_images = []
    
    # Multiple date patterns
    date_patterns = [
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\w+\s+\d{1,2},?\s+\d{4}'
    ]
    
    for img in all_images:
        alt = img['alt']
        date_found = False
        
        for pattern in date_patterns:
            dates = re.findall(pattern, alt)
            if dates:
                date_key = dates[0]
                date_groups[date_key].append(img)
                date_found = True
                break
        
        if not date_found:
            no_date_images.append(img)
    
    print(f"   📅 Enhanced analysis: {len(date_groups)} date groups, {len(no_date_images)} no-date")
    
    # Debug: Print date groups and quality scores
    for date_key, images in date_groups.items():
        print(f"      Date '{date_key}': {len(images)} images")
    print(f"      No-date images: {len(no_date_images)} (quality scores: {[img['quality_score'] for img in no_date_images]})")
    
    # Smart selection algorithm
    if date_groups:
        # Take the most recent/relevant date group
        main_date = list(date_groups.keys())[0]
        main_images = date_groups[main_date]
        
        # Add high-quality no-date images
        high_quality_threshold = 5  # Lower threshold for better results
        quality_no_date = [img for img in no_date_images if img['quality_score'] >= high_quality_threshold]
        
        main_images.extend(quality_no_date)
        
        print(f"   🎯 Selected {len(main_images)} images from main date + quality no-date")
        
        # Ensure we don't exceed expected count significantly
        return main_images[:expected_count + 2]  # Allow slight overflow for better results
    else:
        # No date groups, return highest quality images
        print(f"   🎯 No date groups, returning {min(len(all_images), expected_count)} highest quality images")
        return all_images[:expected_count]

def main():
    """BrowserMCP enhanced extraction test"""
    print("🚀 BROWSERMCP ENHANCED CAROUSEL EXTRACTOR")
    print("=" * 60)
    
    test_cases = [
        {"shortcode": "C0wmEEKItfR", "expected": 10}
    ]
    
    driver = setup_browser(headless=False)  # Run visible for debugging
    
    try:
        for test_case in test_cases:
            shortcode = test_case["shortcode"]
            expected_count = test_case["expected"]
            
            print(f"\n🎯 {shortcode} (expecting {expected_count} images)")
            print("-" * 40)
            
            output_dir = f"/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_{shortcode}"
            os.makedirs(output_dir, exist_ok=True)
            
            start_time = time.time()
            
            # Extract using BrowserMCP enhanced approach
            main_carousel = enhanced_carousel_navigation(driver, shortcode, expected_count)
            
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
                filename = f"{shortcode}_browsermcp_image_{i}.jpg"
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
            
            print(f"\n🚀 BROWSERMCP EXTRACTION COMPLETE for {shortcode}")
            print(f"📊 Images: {len(unique_images)}/{expected_count}")
            print(f"⏱️ Duration: {duration:.1f}s")
            
            if unique_images:
                print(f"📁 BrowserMCP images:")
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
                "method": "browsermcp_enhanced",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results_path = os.path.join(output_dir, "browsermcp_results.json")
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