#!/usr/bin/env python3
"""
Simple Carousel Test - Download 3 images from C0xFHGOrBN7
Uses known working methods from existing codebase
"""

import os
import time
import requests
import hashlib
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


def setup_browser():
    """Setup Chrome browser with Instagram-friendly settings"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1366,768")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def close_popups(driver):
    """Close Instagram popups and modals"""
    print("   🚪 Closing popups...")
    
    # Cookie popup
    try:
        cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Allow all cookies') or contains(text(), 'Accept')]")
        if cookie_btn.is_displayed():
            cookie_btn.click()
            time.sleep(2)
            print("      ✅ Closed cookie popup")
    except:
        pass
    
    # Login popup
    try:
        not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
        if not_now_btn.is_displayed():
            not_now_btn.click()
            time.sleep(2)
            print("      ✅ Closed login popup")
    except:
        pass


def get_main_image(driver):
    """Get the main carousel image URL"""
    try:
        # Find main content images
        images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        for img in images:
            src = img.get_attribute('src')
            if (src and 't51.29350-15' in src and 
                'profile_pic' not in src and img.is_displayed()):
                
                # Check if it's a substantial image (not a small UI element)
                try:
                    size = img.size
                    if size['width'] > 200 and size['height'] > 200:
                        return src
                except:
                    continue
        
        return None
    except Exception as e:
        print(f"      ❌ Error getting image: {e}")
        return None


def download_image(url, filename, download_dir):
    """Download image with proper headers"""
    if not url:
        return False
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if len(response.content) < 5000:  # Too small
            return False
            
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"      ✅ Downloaded: {filename} ({size:,} bytes)")
        return True
        
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False


def navigate_carousel(driver, method_name):
    """Try to navigate to next image in carousel"""
    try:
        if method_name == "keyboard":
            # Use keyboard navigation (user's preferred method)
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            return True
            
        elif method_name == "button":
            # Try clicking next button
            next_selectors = [
                "button[aria-label*='Next']",
                "[role='button'][aria-label*='Next']",
                "button[data-testid*='next']"
            ]
            
            for selector in next_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        ActionChains(driver).move_to_element(btn).click().perform()
                        return True
                except:
                    continue
                    
        elif method_name == "swipe":
            # Simulate swipe gesture
            viewport_width = driver.execute_script("return window.innerWidth")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            start_x = viewport_width * 0.7
            end_x = viewport_width * 0.3
            y = viewport_height * 0.4
            
            actions = ActionChains(driver)
            actions.move_by_offset(start_x, y)
            actions.click_and_hold()
            actions.move_by_offset(end_x - start_x, 0)
            actions.release()
            actions.perform()
            return True
            
        return False
        
    except Exception as e:
        print(f"      ❌ Navigation failed ({method_name}): {e}")
        return False


def extract_carousel_images():
    """Extract all 3 images from C0xFHGOrBN7 carousel"""
    shortcode = "C0xFHGOrBN7"
    download_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(download_dir, exist_ok=True)
    
    print("🎯 SIMPLE CAROUSEL TEST")
    print(f"Target: {shortcode}")
    print(f"Goal: Download 3 images to {download_dir}")
    print("=" * 60)
    
    driver = setup_browser()
    extracted_images = []
    seen_urls = set()
    
    try:
        # Load Instagram post
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"\n📍 Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        close_popups(driver)
        time.sleep(3)
        
        # Extract images using multiple navigation attempts
        navigation_methods = ["keyboard", "button", "swipe"]
        
        for attempt in range(10):  # Try up to 10 navigation attempts
            print(f"\n📸 Extraction attempt {attempt + 1}")
            
            # Get current image
            img_url = get_main_image(driver)
            if img_url and img_url not in seen_urls:
                seen_urls.add(img_url)
                image_num = len(extracted_images) + 1
                filename = f"simple_test_{shortcode}_image_{image_num}.jpg"
                
                if download_image(img_url, filename, download_dir):
                    extracted_images.append({
                        'index': image_num,
                        'filename': filename,
                        'url': img_url
                    })
                    print(f"   ✅ Image {image_num} downloaded successfully")
                else:
                    print(f"   ❌ Failed to download image {image_num}")
            else:
                print(f"   ⚠️ No new image found (duplicate or end of carousel)")
            
            # Stop if we have 3 images
            if len(extracted_images) >= 3:
                print(f"   🎉 All 3 images extracted!")
                break
            
            # Try navigation for next image
            if attempt < 9:  # Don't navigate on last attempt
                method = navigation_methods[attempt % len(navigation_methods)]
                print(f"   🔄 Navigating using {method} method...")
                
                if navigate_carousel(driver, method):
                    print(f"      ✅ Navigation successful")
                    time.sleep(4)  # Wait for new image to load
                else:
                    print(f"      ❌ Navigation failed")
                    time.sleep(2)
        
        # Generate results
        result = {
            'test_name': 'simple_carousel_test',
            'success': len(extracted_images) >= 3,
            'shortcode': shortcode,
            'expected_images': 3,
            'extracted_images': len(extracted_images),
            'downloaded_files': extracted_images,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save test report
        report_file = os.path.join(download_dir, 'simple_test_report.json')
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Print results
        print("\n" + "=" * 60)
        print("🏆 SIMPLE CAROUSEL TEST RESULTS")
        print("=" * 60)
        
        if result['success']:
            print("🎉 TEST PASSED!")
            print(f"✅ Successfully downloaded {len(extracted_images)}/3 images")
        else:
            print("📈 TEST PARTIALLY SUCCESSFUL")
            print(f"⚠️ Downloaded {len(extracted_images)}/3 images")
            print(f"Success rate: {(len(extracted_images)/3)*100:.1f}%")
        
        print(f"\n📁 Downloaded files:")
        for img in extracted_images:
            print(f"   - {img['filename']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return {'success': False, 'error': str(e)}
        
    finally:
        driver.quit()


if __name__ == "__main__":
    result = extract_carousel_images()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 60)
    
    if result.get('success'):
        print("🎉 CAROUSEL EXTRACTION WORKING!")
        print("✅ All 3 images successfully downloaded")
        print("🚀 Test passed - carousel navigation solved!")
    elif result.get('extracted_images', 0) > 0:
        print(f"📈 SIGNIFICANT PROGRESS!")
        print(f"✅ {result.get('extracted_images')} images downloaded")
        print("🔧 Method working, needs minor optimization")
    else:
        print("🔧 NEEDS MORE WORK")
        print("📊 Framework ready, requires refinement")