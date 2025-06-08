#!/usr/bin/env python3
"""
Precise Carousel Extractor - Properly navigate carousel and avoid duplicates
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

def get_main_carousel_image(driver):
    """Get the main carousel image from current view"""
    # Focus on main article content only
    selectors = [
        "article[role='presentation'] img[src*='1440x']",
        "article[role='presentation'] img[src*='1080x']",
        "main article img[src*='1440x']",
        "main article img[src*='1080x']",
        "article img[src*='t51.29350-15'][src*='1440x']",
        "article img[src*='t51.29350-15'][src*='1080x']"
    ]
    
    for selector in selectors:
        try:
            images = driver.find_elements(By.CSS_SELECTOR, selector)
            for img in images:
                src = img.get_attribute('src')
                # Ensure it's a main content image, not profile/avatar
                if (src and 't51.29350-15' in src and 
                    not any(exclude in src for exclude in ['profile', 'avatar', 's150x150', 's320x320'])):
                    return src
        except:
            continue
    
    return None

def navigate_carousel(driver, shortcode, output_dir):
    """Navigate carousel properly with Next button clicks"""
    print("\n🎠 Navigating carousel with proper Next button clicks")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(5)
    
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
        image_url = get_main_carousel_image(driver)
        if image_url:
            filename = f"{shortcode}_image_1.jpg"
            filepath = os.path.join(output_dir, filename)
            success, img_hash = download_if_new(image_url, filepath, existing_hashes, headers)
            if success:
                images_downloaded.append((image_url, 1))
    else:
        print(f"  🎠 Carousel detected with {len(carousel_indicators)} navigation elements")
        
        # Navigate through carousel positions
        max_positions = 10  # Safety limit
        position = 1
        
        while position <= max_positions:
            print(f"  📍 Getting carousel image at position {position}")
            
            # Wait for image to load
            time.sleep(2)
            
            # Get the main image at current position
            image_url = get_main_carousel_image(driver)
            
            if image_url:
                filename = f"{shortcode}_image_{position}.jpg"
                filepath = os.path.join(output_dir, filename)
                success, img_hash = download_if_new(image_url, filepath, existing_hashes, headers)
                if success:
                    images_downloaded.append((image_url, position))
            else:
                print(f"    ⚠️ No main image found at position {position}")
            
            # Try to click Next button for next position
            if position < max_positions:
                next_clicked = False
                
                # Enhanced Next button selectors
                next_selectors = [
                    "button[aria-label*='Next']",
                    "button[aria-label*='next']",
                    "[role='button'][aria-label*='Next']",
                    "[aria-label*='Go to slide " + str(position + 1) + "']",
                    "button:has(svg[aria-label*='Next'])",
                    "article button[aria-label*='Next']",
                    "main button[aria-label*='Next']"
                ]
                
                for selector in next_selectors:
                    try:
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in next_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                # Scroll into view and click
                                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(0.5)
                                
                                # Try clicking with JavaScript if regular click fails
                                try:
                                    ActionChains(driver).move_to_element(btn).click().perform()
                                except:
                                    driver.execute_script("arguments[0].click();", btn)
                                
                                print(f"    ➡️ Clicked Next button (position {position} → {position + 1})")
                                time.sleep(2)  # Wait for transition
                                next_clicked = True
                                break
                        
                        if next_clicked:
                            break
                    except Exception as e:
                        continue
                
                if not next_clicked:
                    print(f"    🛑 No more Next button found - end of carousel at position {position}")
                    break
                    
            position += 1
    
    print(f"  📊 Carousel navigation complete: {len(images_downloaded)} unique images")
    return images_downloaded

def extract_carousel_instagram_api_style(shortcode, output_dir):
    """
    For 2000+ posts, we need Instagram Basic Display API or Graph API.
    However, these require:
    1. User authentication and permissions
    2. Business account verification for Graph API  
    3. Only work for content you own/have permission to access
    
    For public posts at scale, browser automation with rate limiting is the most reliable approach.
    """
    print("📋 Instagram API Options for 2000+ Posts:")
    print("  🔐 Basic Display API: Requires user auth, limited to user's own content")
    print("  🏢 Graph API: Business accounts only, requires Facebook approval")
    print("  📝 oEmbed API: Only basic post info, no carousel images")
    print("  ⚠️  No official API for public post carousel extraction at scale")
    print("  ✅ Browser automation with rate limiting is most reliable for 2000+ posts")

def main():
    """Extract carousel with proper navigation and duplicate prevention"""
    print("🎯 PRECISE CAROUSEL EXTRACTION WITH PROPER NAVIGATION")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Clean output directory of old images
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.startswith(shortcode) and file.endswith(('.jpg', '.png', '.jpeg')):
                os.remove(os.path.join(output_dir, file))
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    
    try:
        # Extract carousel with proper navigation
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
        
        # Address scaling question
        print(f"\n💡 For 2000+ posts automation:")
        extract_carousel_instagram_api_style(shortcode, output_dir)
        
        return success
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()