#!/usr/bin/env python3
"""
Flexible Carousel Extractor - Better selectors and debugging
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

def download_if_new(url: str, filepath: str, existing_hashes: set, headers: dict) -> tuple:
    """Download image only if it's not a duplicate"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Check if this image is a duplicate
        image_hash = get_image_hash(response.content)
        if image_hash in existing_hashes:
            print(f"    🔄 Skipping duplicate: {os.path.basename(filepath)}")
            return False, image_hash
        
        # Save new image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        existing_hashes.add(image_hash)
        print(f"    ✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return True, image_hash
        
    except Exception as e:
        print(f"    ❌ Failed: {os.path.basename(filepath)} - {e}")
        return False, None

def close_popups(driver):
    """Close all popups and modals"""
    print("  🚪 Closing popups...")
    
    popup_selectors = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow')]", 
        "//button[contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Not now')]",
        "//button[@aria-label='Close']",
        "//button[contains(@aria-label, 'Close')]"
    ]
    
    for selector in popup_selectors:
        try:
            wait = WebDriverWait(driver, 2)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            element.click()
            print(f"    ❌ Closed popup")
            time.sleep(1)
            break
        except:
            continue

def debug_available_images(driver):
    """Debug what images are available on the page"""
    print("    🔍 Debugging available images...")
    
    all_images = driver.find_elements(By.CSS_SELECTOR, "img")
    instagram_images = []
    
    for i, img in enumerate(all_images):
        src = img.get_attribute('src')
        alt = img.get_attribute('alt') or ''
        
        if src and ('instagram' in src or 'fbcdn' in src or 'scontent' in src):
            instagram_images.append({
                'index': i,
                'src': src[:100] + '...' if len(src) > 100 else src,
                'alt': alt[:50] + '...' if len(alt) > 50 else alt,
                'full_src': src
            })
    
    print(f"    📊 Found {len(instagram_images)} Instagram images:")
    for img in instagram_images[:10]:  # Show first 10
        print(f"      {img['index']}: {img['src']}")
        if img['alt']:
            print(f"           Alt: {img['alt']}")
    
    return [img['full_src'] for img in instagram_images]

def get_main_carousel_image(driver, debug=False):
    """Get the main carousel image from current view with flexible selectors"""
    if debug:
        all_urls = debug_available_images(driver)
    
    # Progressive selector strategy - from most specific to most general
    selector_groups = [
        # Group 1: High-quality main content images
        [
            "article img[src*='1440x']",
            "article img[src*='1080x']",
            "main img[src*='1440x']", 
            "main img[src*='1080x']"
        ],
        # Group 2: Medium quality main content
        [
            "article img[src*='t51.29350-15']",
            "main img[src*='t51.29350-15']"
        ],
        # Group 3: Any main content images  
        [
            "article img[src*='scontent']",
            "main img[src*='scontent']",
            "article img[src*='fbcdn']",
            "main img[src*='fbcdn']"
        ],
        # Group 4: Fallback to any content images
        [
            "img[src*='t51.29350-15']",
            "img[src*='1440x']",
            "img[src*='1080x']"
        ]
    ]
    
    for group_idx, selectors in enumerate(selector_groups, 1):
        print(f"      🎯 Trying selector group {group_idx}...")
        
        for selector in selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"        📊 {selector}: found {len(images)} images")
                
                for img in images:
                    src = img.get_attribute('src')
                    if (src and 
                        # Exclude obvious non-content images
                        not any(exclude in src.lower() for exclude in [
                            'profile', 'avatar', 's150x150', 's320x320', 's640x640'
                        ])):
                        print(f"        ✅ Selected image: {src[:80]}...")
                        return src
            except Exception as e:
                print(f"        ⚠️ Selector failed: {e}")
                continue
    
    print("      ❌ No suitable image found with any selector")
    return None

def navigate_carousel(driver, shortcode, output_dir):
    """Navigate carousel properly with Next button clicks"""
    print("\n🎠 Navigating carousel with proper Next button clicks")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)  # Longer initial wait
    
    close_popups(driver)
    time.sleep(3)
    
    images_downloaded = []
    existing_hashes = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Check if this is a carousel
    carousel_indicators = driver.find_elements(By.CSS_SELECTOR, 
        "button[aria-label*='Next'], [aria-label*='Go to slide'], [role='button'][aria-label*='Next']")
    
    if not carousel_indicators:
        print("  📷 Single post detected - no carousel navigation needed")
        # Just get the single image
        image_url = get_main_carousel_image(driver, debug=True)
        if image_url:
            filename = f"{shortcode}_image_1.jpg"
            filepath = os.path.join(output_dir, filename)
            success, img_hash = download_if_new(image_url, filepath, existing_hashes, headers)
            if success:
                images_downloaded.append((image_url, 1))
    else:
        print(f"  🎠 Carousel detected with {len(carousel_indicators)} navigation elements")
        
        # Navigate through carousel positions
        max_positions = 5  # Reduced safety limit since we know there are 3
        position = 1
        consecutive_failures = 0
        
        while position <= max_positions and consecutive_failures < 2:
            print(f"  📍 Getting carousel image at position {position}")
            
            # Wait for image to load and carousel to settle
            time.sleep(3)
            
            # Get the main image at current position
            image_url = get_main_carousel_image(driver, debug=(position==1))
            
            if image_url:
                filename = f"{shortcode}_image_{position}.jpg"
                filepath = os.path.join(output_dir, filename)
                success, img_hash = download_if_new(image_url, filepath, existing_hashes, headers)
                if success:
                    images_downloaded.append((image_url, position))
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
            else:
                print(f"    ⚠️ No main image found at position {position}")
                consecutive_failures += 1
            
            # Try to click Next button for next position
            if position < max_positions:
                next_clicked = False
                
                # Wait a bit before trying to click Next
                time.sleep(1)
                
                # Enhanced Next button selectors
                next_selectors = [
                    "button[aria-label*='Next']",
                    "button[aria-label*='next']",
                    "[role='button'][aria-label*='Next']",
                    "button:has(svg[aria-label*='Next'])",
                    "article button[aria-label*='Next']",
                    "main button[aria-label*='Next']",
                    "[data-testid*='next']",
                    "button[data-testid*='carousel-next']"
                ]
                
                for selector in next_selectors:
                    try:
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in next_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                # Scroll into view first
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(0.5)
                                
                                # Try multiple click methods
                                try:
                                    # Method 1: ActionChains
                                    ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
                                except:
                                    try:
                                        # Method 2: Direct click
                                        btn.click()
                                    except:
                                        # Method 3: JavaScript click
                                        driver.execute_script("arguments[0].click();", btn)
                                
                                print(f"    ➡️ Clicked Next button (position {position} → {position + 1})")
                                time.sleep(2)  # Wait for carousel transition
                                next_clicked = True
                                break
                        
                        if next_clicked:
                            break
                    except Exception as e:
                        print(f"    ⚠️ Next button selector failed: {e}")
                        continue
                
                if not next_clicked:
                    print(f"    🛑 No more Next button found - end of carousel at position {position}")
                    break
                    
            position += 1
    
    print(f"  📊 Carousel navigation complete: {len(images_downloaded)} unique images")
    return images_downloaded

def main():
    """Extract carousel with improved navigation and better selectors"""
    print("🎯 FLEXIBLE CAROUSEL EXTRACTION WITH BETTER SELECTORS")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Clean output directory of old images from this extraction
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.startswith(shortcode) and file.endswith(('.jpg', '.png', '.jpeg')):
                os.remove(os.path.join(output_dir, file))
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    
    try:
        # Extract carousel with improved navigation
        results = navigate_carousel(driver, shortcode, output_dir)
        
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Unique images extracted: {len(results)}")
        print(f"🎯 Expected for carousel: 3 images")
        
        # List final images
        final_images = [f for f in os.listdir(output_dir) if f.startswith(shortcode) and f.endswith(('.jpg', '.png', '.jpeg'))]
        print(f"\n📁 Final extracted images:")
        for img in sorted(final_images):
            filepath = os.path.join(output_dir, img)
            size = os.path.getsize(filepath)
            print(f"  ✅ {img} ({size} bytes)")
        
        success = len(final_images) >= 3
        print(f"\n{'🎊 SUCCESS' if success else '⚠️ PARTIAL'}: {len(final_images)} images extracted")
        
        return success
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()