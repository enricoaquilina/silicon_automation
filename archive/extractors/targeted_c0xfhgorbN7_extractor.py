#!/usr/bin/env python3
"""
Targeted C0xFHGOrBN7 Extractor - Get exactly 3 unique carousel images
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

def extract_carousel_with_navigation(driver, shortcode, output_dir):
    """Extract carousel by manually navigating through positions"""
    print("🎠 Starting carousel extraction with manual navigation")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)
    
    close_popups(driver)
    time.sleep(3)
    
    unique_images = []
    existing_hashes = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Navigate through carousel positions
    max_attempts = 6  # Try harder to find all 3 images
    position = 1
    
    while position <= max_attempts and len(unique_images) < 3:
        print(f"\n📍 Position {position}: Looking for carousel image...")
        
        # Wait for content to stabilize
        time.sleep(3)
        
        # Try multiple strategies to find the main image
        found_image = False
        
        # Strategy 1: Look in main article
        try:
            main_imgs = driver.find_elements(By.CSS_SELECTOR, "main article img")
            for img in main_imgs:
                src = img.get_attribute('src')
                if (src and 't51.29350-15' in src and 
                    not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                    
                    filename = f"C0xFHGOrBN7_image_{len(unique_images) + 1}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    success, img_hash, size = download_unique_image(src, filepath, existing_hashes, headers)
                    if success:
                        unique_images.append({
                            'position': position,
                            'url': src,
                            'filename': filename,
                            'size': size,
                            'hash': img_hash
                        })
                        found_image = True
                        print(f"   📸 Found image {len(unique_images)}/3 at position {position}")
                        break
        except:
            pass
        
        # Strategy 2: Look in any article if main failed
        if not found_image:
            try:
                all_imgs = driver.find_elements(By.CSS_SELECTOR, "article img")
                for img in all_imgs:
                    src = img.get_attribute('src')
                    if (src and 't51.29350-15' in src and 
                        not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                        
                        filename = f"C0xFHGOrBN7_image_{len(unique_images) + 1}.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        success, img_hash, size = download_unique_image(src, filepath, existing_hashes, headers)
                        if success:
                            unique_images.append({
                                'position': position,
                                'url': src,
                                'filename': filename,
                                'size': size,
                                'hash': img_hash
                            })
                            found_image = True
                            print(f"   📸 Found image {len(unique_images)}/3 at position {position}")
                            break
            except:
                pass
        
        if not found_image:
            print(f"   ⚠️ No new image found at position {position}")
        
        # Try to navigate to next position if we need more images
        if len(unique_images) < 3 and position < max_attempts:
            print(f"   ➡️ Attempting to navigate to position {position + 1}")
            
            # Try multiple next button strategies
            next_clicked = False
            next_selectors = [
                "button[aria-label*='Next']",
                "button[aria-label*='next']",
                "[role='button'][aria-label*='Next']",
                "article button[aria-label*='Next']",
                "main button[aria-label*='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in next_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            # Scroll to button
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)
                            
                            # Try clicking
                            try:
                                ActionChains(driver).move_to_element(btn).click().perform()
                            except:
                                driver.execute_script("arguments[0].click();", btn)
                            
                            print(f"      ✅ Clicked Next button")
                            time.sleep(2)
                            next_clicked = True
                            break
                    
                    if next_clicked:
                        break
                except:
                    continue
            
            if not next_clicked:
                print(f"      ❌ Could not find/click Next button")
                # Try keyboard navigation as fallback
                try:
                    from selenium.webdriver.common.keys import Keys
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ARROW_RIGHT)
                    print(f"      ⌨️ Tried keyboard navigation")
                    time.sleep(2)
                except:
                    pass
        
        position += 1
    
    return unique_images

def main():
    """Extract exactly 3 unique carousel images"""
    print("🎯 TARGETED C0xFHGOrBN7 CAROUSEL EXTRACTION")
    print("=" * 60)
    print("Goal: Extract exactly 3 unique carousel images")
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    
    try:
        # Extract carousel images
        unique_images = extract_carousel_with_navigation(driver, shortcode, output_dir)
        
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Unique images extracted: {len(unique_images)}")
        print(f"🎯 Target: 3 images")
        
        # Display results
        if unique_images:
            print(f"\n📁 Successfully extracted images:")
            for i, img in enumerate(unique_images, 1):
                print(f"  {i}. {img['filename']} ({img['size']} bytes)")
                print(f"     Position: {img['position']}, Hash: {img['hash'][:12]}...")
        
        # Save extraction info
        extraction_info = {
            "shortcode": shortcode,
            "target_images": 3,
            "extracted_images": len(unique_images),
            "success": len(unique_images) >= 3,
            "images": unique_images,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        info_path = os.path.join(output_dir, "extraction_info.json")
        with open(info_path, 'w') as f:
            json.dump(extraction_info, f, indent=2)
        
        # Final status
        if len(unique_images) >= 3:
            print(f"\n🎊 SUCCESS: All 3 carousel images extracted!")
        else:
            print(f"\n⚠️ PARTIAL: Only {len(unique_images)}/3 images extracted")
            print("   Possible reasons:")
            print("   - Carousel has fewer than 3 images")
            print("   - Navigation buttons not working")
            print("   - Instagram changed their structure")
        
        return len(unique_images) >= 3
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()