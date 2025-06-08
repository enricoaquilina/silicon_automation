#!/usr/bin/env python3
"""
Headless Computer Vision Carousel Extractor - More precise navigation
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

def get_current_carousel_images(driver):
    """Get all high-quality carousel images currently visible"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='t51.29350-15']")
    
    carousel_images = []
    for img in images:
        try:
            src = img.get_attribute('src')
            if (src and 't51.29350-15' in src and 
                not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320']) and
                ('1440x' in src or '1080x' in src or src.endswith('.jpg'))):
                
                carousel_images.append(src)
        except:
            continue
    
    return list(set(carousel_images))  # Remove duplicates

def navigate_carousel_systematically(driver, shortcode, expected_count):
    """Navigate carousel systematically using multiple methods"""
    print(f"🎯 Systematic carousel navigation for {shortcode}")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)
    
    close_popups(driver)
    time.sleep(3)
    
    all_unique_urls = set()
    
    # Method 1: Collect initial images
    print("📍 Method 1: Collecting initial visible images...")
    initial_images = get_current_carousel_images(driver)
    for img in initial_images:
        all_unique_urls.add(img)
        print(f"   🖼️ Initial image: {img[:60]}...")
    
    # Method 2: Try navigation with Next buttons
    print("📍 Method 2: Navigation with Next buttons...")
    for attempt in range(expected_count + 5):  # Try more than expected
        print(f"   🔄 Navigation attempt {attempt + 1}")
        
        # Look for Next buttons
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='next']",
            "[role='button'][aria-label*='Next']",
            "article button[aria-label*='Next']",
            "main button[aria-label*='Next']"
        ]
        
        clicked = False
        for selector in next_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        # Try multiple click methods
                        try:
                            ActionChains(driver).move_to_element(button).click().perform()
                        except:
                            try:
                                button.click()
                            except:
                                driver.execute_script("arguments[0].click();", button)
                        
                        print(f"      ✅ Clicked Next button")
                        time.sleep(3)
                        clicked = True
                        break
                if clicked:
                    break
            except:
                continue
        
        if clicked:
            # Collect new images after navigation
            new_images = get_current_carousel_images(driver)
            new_count = 0
            for img in new_images:
                if img not in all_unique_urls:
                    all_unique_urls.add(img)
                    new_count += 1
                    print(f"      🆕 New image after navigation: {img[:60]}...")
            
            if new_count == 0:
                print(f"      ⚠️ No new images found after click")
        else:
            print(f"      ❌ Could not click Next button")
            break
    
    # Method 3: Keyboard navigation
    print("📍 Method 3: Keyboard navigation...")
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        for key_attempt in range(expected_count):
            body.send_keys(Keys.ARROW_RIGHT)
            time.sleep(2)
            
            new_images = get_current_carousel_images(driver)
            for img in new_images:
                if img not in all_unique_urls:
                    all_unique_urls.add(img)
                    print(f"   ⌨️ New image via keyboard: {img[:60]}...")
    except:
        print("   ⚠️ Keyboard navigation failed")
    
    # Method 4: Try clicking on carousel dots/indicators
    print("📍 Method 4: Carousel indicators...")
    try:
        for slide_num in range(1, expected_count + 1):
            dot_selectors = [
                f"[aria-label*='Go to slide {slide_num}']",
                f"button[aria-label*='{slide_num}']",
                f"[data-slide-to='{slide_num}']"
            ]
            
            for selector in dot_selectors:
                try:
                    dots = driver.find_elements(By.CSS_SELECTOR, selector)
                    for dot in dots:
                        if dot.is_displayed() and dot.is_enabled():
                            dot.click()
                            time.sleep(2)
                            
                            new_images = get_current_carousel_images(driver)
                            for img in new_images:
                                if img not in all_unique_urls:
                                    all_unique_urls.add(img)
                                    print(f"   🔘 New image via indicator: {img[:60]}...")
                except:
                    continue
    except:
        print("   ⚠️ Carousel indicators not found")
    
    # Method 5: Force page interactions to trigger loading
    print("📍 Method 5: Force interactions...")
    try:
        # Click in different areas of the page
        for x_offset in [-100, 0, 100]:
            for y_offset in [-50, 0, 50]:
                try:
                    ActionChains(driver).move_by_offset(x_offset, y_offset).click().perform()
                    time.sleep(1)
                    ActionChains(driver).move_by_offset(-x_offset, -y_offset).perform()  # Reset
                except:
                    continue
        
        # Collect any new images
        final_images = get_current_carousel_images(driver)
        for img in final_images:
            if img not in all_unique_urls:
                all_unique_urls.add(img)
                print(f"   🖱️ New image via interaction: {img[:60]}...")
    except:
        print("   ⚠️ Force interactions failed")
    
    print(f"\n📊 Systematic navigation complete: {len(all_unique_urls)} unique URLs found")
    return list(all_unique_urls)

def main():
    """Test systematic carousel extraction"""
    print("🎯 HEADLESS SYSTEMATIC CAROUSEL EXTRACTOR")
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
            
            # Extract using systematic navigation
            carousel_urls = navigate_carousel_systematically(driver, shortcode, expected_count)
            
            if not carousel_urls:
                print(f"❌ No images found for {shortcode}")
                continue
            
            print(f"\n📥 Downloading {len(carousel_urls)} images...")
            
            unique_images = []
            existing_hashes = set()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.instagram.com/'
            }
            
            # Download images
            for i, url in enumerate(carousel_urls, 1):
                filename = f"{shortcode}_systematic_image_{i}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                success, img_hash, size = download_unique_image(url, filepath, existing_hashes, headers)
                if success:
                    unique_images.append({
                        'index': i,
                        'url': url,
                        'filename': filename,
                        'size': size,
                        'hash': img_hash
                    })
                    
                    # Stop if we have enough
                    if len(unique_images) >= expected_count:
                        print(f"   🎯 Reached target of {expected_count} images")
                        break
            
            print(f"\n🎉 SYSTEMATIC EXTRACTION COMPLETE for {shortcode}")
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
                "method": "systematic_navigation",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results_path = os.path.join(output_dir, "systematic_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            if len(unique_images) >= expected_count:
                print(f"🎊 SUCCESS: All {expected_count} images extracted for {shortcode}!")
            else:
                print(f"⚠️ PARTIAL: Only {len(unique_images)}/{expected_count} images for {shortcode}")
            
            print(f"📁 Results saved to: systematic_results.json")
            print(f"\n" + "=" * 60)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()