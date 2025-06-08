#!/usr/bin/env python3
"""
Computer Vision Carousel Extractor - Use visual recognition and precise mouse control
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
from PIL import Image
import io
import base64

def setup_browser():
    """Setup browser with anti-detection and visual capabilities"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1920,1080")
    # Don't use headless mode so we can see what's happening
    # options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def take_screenshot(driver, filepath):
    """Take screenshot for visual debugging"""
    driver.save_screenshot(filepath)
    print(f"📸 Screenshot saved: {filepath}")

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
    """Close all popups with visual confirmation"""
    print("🚪 Closing popups with visual confirmation...")
    
    # Take screenshot before popup handling
    take_screenshot(driver, "/tmp/before_popup_handling.png")
    
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
            wait = WebDriverWait(driver, 3)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            
            # Highlight the element we're about to click
            driver.execute_script("arguments[0].style.border='3px solid red'", element)
            time.sleep(1)
            
            element.click()
            print(f"✅ Clicked popup button: {selector}")
            time.sleep(2)
            
            # Take screenshot after clicking
            take_screenshot(driver, "/tmp/after_popup_click.png")
            break
        except:
            continue

def find_carousel_navigation_buttons(driver):
    """Find carousel navigation buttons using visual inspection"""
    print("🔍 Looking for carousel navigation buttons...")
    
    # Take screenshot to see current state
    take_screenshot(driver, "/tmp/looking_for_buttons.png")
    
    # Try multiple button selectors with visual confirmation
    button_selectors = [
        "button[aria-label*='Next']",
        "button[aria-label*='next']",
        "[role='button'][aria-label*='Next']",
        "article button[aria-label*='Next']",
        "main button[aria-label*='Next']",
        "button[data-testid*='next']",
        "button[data-testid*='carousel-next']",
        ".carousel-control-next",
        "[aria-label*='Go to slide']"
    ]
    
    found_buttons = []
    
    for selector in button_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for i, button in enumerate(buttons):
                if button.is_displayed() and button.is_enabled():
                    # Highlight found button
                    driver.execute_script("arguments[0].style.border='3px solid green'", button)
                    
                    button_info = {
                        'element': button,
                        'selector': selector,
                        'index': i,
                        'text': button.text,
                        'aria_label': button.get_attribute('aria-label'),
                        'location': button.location,
                        'size': button.size
                    }
                    found_buttons.append(button_info)
                    
                    print(f"🎯 Found button: {selector} - {button.get_attribute('aria-label')} at {button.location}")
        except Exception as e:
            print(f"⚠️ Selector failed: {selector} - {e}")
    
    if found_buttons:
        take_screenshot(driver, "/tmp/found_buttons_highlighted.png")
        print(f"📊 Found {len(found_buttons)} navigation buttons")
    else:
        print("❌ No navigation buttons found")
    
    return found_buttons

def scroll_and_look_for_images(driver):
    """Scroll around to make sure all content is loaded"""
    print("📜 Scrolling to load all content...")
    
    # Scroll down
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    take_screenshot(driver, "/tmp/scrolled_down.png")
    
    # Scroll back up
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    take_screenshot(driver, "/tmp/scrolled_up.png")
    
    # Try horizontal scrolling on main content
    try:
        main_content = driver.find_element(By.CSS_SELECTOR, "main")
        ActionChains(driver).move_to_element(main_content).perform()
        time.sleep(1)
        
        # Try arrow keys
        main_content.send_keys(Keys.ARROW_RIGHT)
        time.sleep(2)
        take_screenshot(driver, "/tmp/arrow_right.png")
        
        main_content.send_keys(Keys.ARROW_LEFT)
        time.sleep(2)
        take_screenshot(driver, "/tmp/arrow_left.png")
    except:
        print("⚠️ Could not use arrow keys on main content")

def extract_images_with_computer_vision(driver):
    """Extract images using computer vision approach"""
    print("👁️ Extracting images with computer vision...")
    
    # Get all images currently visible
    images = driver.find_elements(By.CSS_SELECTOR, "img")
    
    carousel_images = []
    for i, img in enumerate(images):
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            if (src and 't51.29350-15' in src and 
                not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                
                # Highlight this image
                driver.execute_script("arguments[0].style.border='3px solid blue'", img)
                
                carousel_images.append({
                    'src': src,
                    'alt': alt,
                    'location': img.location,
                    'size': img.size,
                    'index': i
                })
                
                print(f"🖼️ Found carousel image {len(carousel_images)}: {src[:80]}...")
        except:
            continue
    
    # Take screenshot showing highlighted images
    take_screenshot(driver, "/tmp/highlighted_images.png")
    
    return carousel_images

def computer_vision_carousel_navigation(driver, shortcode, expected_count):
    """Navigate carousel using computer vision and mouse control"""
    print(f"🖱️ Starting computer vision navigation for {shortcode}")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(10)
    
    # Take initial screenshot
    take_screenshot(driver, f"/tmp/{shortcode}_initial.png")
    
    close_popups(driver)
    time.sleep(3)
    
    # Scroll to load content
    scroll_and_look_for_images(driver)
    
    collected_images = set()
    position = 0
    max_positions = expected_count + 3
    
    while position < max_positions and len(collected_images) < expected_count:
        position += 1
        print(f"\n📍 Position {position}: Using computer vision approach...")
        
        # Take screenshot of current position
        take_screenshot(driver, f"/tmp/{shortcode}_position_{position}.png")
        
        # Extract images at current position
        current_images = extract_images_with_computer_vision(driver)
        
        # Add new unique images
        new_images_found = False
        for img in current_images:
            if img['src'] not in collected_images:
                collected_images.add(img['src'])
                new_images_found = True
                print(f"   🆕 New image found: {img['src'][:60]}...")
        
        if not new_images_found:
            print(f"   ⚠️ No new images at position {position}")
        
        # Stop if we have enough
        if len(collected_images) >= expected_count:
            print(f"   🎯 Collected {len(collected_images)} images (target: {expected_count})")
            break
        
        # Try to navigate to next position
        print(f"   ➡️ Attempting navigation to position {position + 1}")
        
        # Find navigation buttons
        nav_buttons = find_carousel_navigation_buttons(driver)
        
        if nav_buttons:
            # Try clicking the first suitable button
            for button_info in nav_buttons:
                try:
                    button = button_info['element']
                    
                    # Scroll button into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(1)
                    
                    # Highlight before clicking
                    driver.execute_script("arguments[0].style.border='5px solid red'", button)
                    time.sleep(1)
                    
                    # Click using ActionChains for more human-like interaction
                    ActionChains(driver).move_to_element(button).pause(0.5).click().perform()
                    
                    print(f"      ✅ Clicked navigation button: {button_info['aria_label']}")
                    time.sleep(3)  # Wait longer for transition
                    
                    # Take screenshot after click
                    take_screenshot(driver, f"/tmp/{shortcode}_after_click_{position}.png")
                    break
                    
                except Exception as e:
                    print(f"      ⚠️ Failed to click button: {e}")
                    continue
        else:
            print(f"      ❌ No navigation buttons found")
            # Try keyboard navigation as fallback
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.ARROW_RIGHT)
                print(f"      ⌨️ Used keyboard navigation")
                time.sleep(2)
            except:
                print(f"      ❌ Keyboard navigation failed")
    
    print(f"\n📊 Computer vision navigation complete: {len(collected_images)} unique images")
    return list(collected_images)

def main():
    """Test computer vision carousel extraction"""
    print("👁️ COMPUTER VISION CAROUSEL EXTRACTOR")
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
            
            # Extract using computer vision
            carousel_urls = computer_vision_carousel_navigation(driver, shortcode, expected_count)
            
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
                filename = f"{shortcode}_cv_image_{i}.jpg"
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
            
            print(f"\n🎉 COMPUTER VISION EXTRACTION COMPLETE for {shortcode}")
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
                "method": "computer_vision_navigation",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results_path = os.path.join(output_dir, "computer_vision_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            if len(unique_images) >= expected_count:
                print(f"🎊 SUCCESS: All {expected_count} images extracted for {shortcode}!")
            else:
                print(f"⚠️ PARTIAL: Only {len(unique_images)}/{expected_count} images for {shortcode}")
            
            print(f"\n📸 Screenshots saved to /tmp/ for debugging")
            print(f"📁 Results saved to: computer_vision_results.json")
            print(f"\n" + "=" * 60)
    
    finally:
        try:
            input("Press Enter to close browser and continue...")
        except EOFError:
            print("Closing browser automatically...")
        driver.quit()

if __name__ == "__main__":
    main()