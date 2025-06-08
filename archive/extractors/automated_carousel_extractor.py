#!/usr/bin/env python3
"""
Automated Carousel Extractor - Find carousel URLs automatically via browser automation
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

def navigate_and_collect_images(driver, shortcode, expected_count):
    """Navigate through carousel collecting all image URLs"""
    print(f"🎠 Navigating carousel for {shortcode} (expecting {expected_count} images)")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)
    
    close_popups(driver)
    time.sleep(3)
    
    collected_urls = set()
    position = 0
    max_positions = expected_count + 5  # Give some buffer
    consecutive_failures = 0
    
    while position < max_positions and consecutive_failures < 3:
        position += 1
        print(f"\n📍 Position {position}: Collecting image URLs...")
        
        # Wait for content to load
        time.sleep(3)
        
        # Method 1: Get current visible high-quality images
        found_new_urls = False
        
        # Try multiple strategies to find current carousel image
        selectors = [
            "article img[src*='t51.29350-15']",
            "main img[src*='t51.29350-15']", 
            "div[role='presentation'] img[src*='t51.29350-15']",
            "img[src*='t51.29350-15'][src*='1440x']",
            "img[src*='t51.29350-15'][src*='1080x']"
        ]
        
        for selector in selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    src = img.get_attribute('src')
                    if (src and 't51.29350-15' in src and 
                        not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
                        src not in collected_urls):
                        
                        collected_urls.add(src)
                        print(f"   🖼️ Found new image URL: {src[:80]}...")
                        found_new_urls = True
            except:
                continue
        
        # Method 2: Check page source for any new URLs
        try:
            page_source = driver.page_source
            pattern = r'https://[^"\']*t51\.29350-15[^"\']*\.jpg[^"\']*'
            matches = re.findall(pattern, page_source)
            
            for match in matches:
                clean_url = match.split('\\')[0].split('"')[0].split("'")[0]
                if (not any(ex in clean_url.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
                    clean_url not in collected_urls and
                    ('1440x' in clean_url or '1080x' in clean_url or 'jpg' in clean_url)):
                    collected_urls.add(clean_url)
                    print(f"   🔍 Found in source: {clean_url[:80]}...")
                    found_new_urls = True
        except:
            pass
        
        if found_new_urls:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            print(f"   ⚠️ No new images found at position {position}")
        
        # Stop if we have enough images
        if len(collected_urls) >= expected_count:
            print(f"   🎯 Collected {len(collected_urls)} URLs (target: {expected_count})")
            break
        
        # Try to navigate to next image
        if position < max_positions:
            print(f"   ➡️ Attempting to navigate to position {position + 1}")
            
            # Try multiple navigation methods
            navigated = False
            
            # Method 1: Click Next button
            next_selectors = [
                "button[aria-label*='Next']",
                "button[aria-label*='next']",
                "[role='button'][aria-label*='Next']",
                "article button[aria-label*='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in next_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)
                            
                            try:
                                ActionChains(driver).move_to_element(btn).click().perform()
                            except:
                                driver.execute_script("arguments[0].click();", btn)
                            
                            print(f"      ✅ Clicked Next button")
                            time.sleep(2)
                            navigated = True
                            break
                    
                    if navigated:
                        break
                except:
                    continue
            
            # Method 2: Keyboard navigation
            if not navigated:
                try:
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ARROW_RIGHT)
                    print(f"      ⌨️ Used keyboard navigation")
                    time.sleep(2)
                    navigated = True
                except:
                    pass
            
            # Method 3: Click on carousel dots/indicators
            if not navigated:
                try:
                    dot_selectors = [
                        f"[aria-label*='Go to slide {position + 1}']",
                        f"button[aria-label*='{position + 1}']",
                        ".carousel-indicator",
                        "[role='tablist'] button"
                    ]
                    
                    for selector in dot_selectors:
                        dots = driver.find_elements(By.CSS_SELECTOR, selector)
                        for dot in dots:
                            if dot.is_displayed() and dot.is_enabled():
                                dot.click()
                                print(f"      🔘 Clicked carousel indicator")
                                time.sleep(2)
                                navigated = True
                                break
                        if navigated:
                            break
                except:
                    pass
            
            if not navigated:
                print(f"      ❌ Could not navigate to next position")
    
    print(f"\n📊 Collection complete: {len(collected_urls)} unique URLs found")
    return list(collected_urls)

def extract_carousel_automated(driver, shortcode, output_dir, expected_count):
    """Extract carousel using automated navigation"""
    print(f"🎯 Starting automated extraction for {shortcode}")
    
    # Collect all carousel URLs
    carousel_urls = navigate_and_collect_images(driver, shortcode, expected_count)
    
    if not carousel_urls:
        print("❌ No carousel URLs found")
        return []
    
    print(f"\n📥 Downloading {len(carousel_urls)} unique images...")
    
    unique_images = []
    existing_hashes = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Download all unique images
    for i, url in enumerate(carousel_urls, 1):
        print(f"\n📍 Processing image {i}/{len(carousel_urls)}")
        
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
            
            # Stop if we have enough images
            if len(unique_images) >= expected_count:
                print(f"   🎯 Reached target of {expected_count} images")
                break
    
    return unique_images

def main():
    """Test automated extraction on both carousels"""
    print("🎯 AUTOMATED CAROUSEL EXTRACTOR")
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
            
            # Extract images
            unique_images = extract_carousel_automated(driver, shortcode, output_dir, expected_count)
            
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
                "method": "automated_navigation",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            info_path = os.path.join(output_dir, "automated_extraction_info.json")
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