#!/usr/bin/env python3
"""
Target the specific visual next button (small > on right side)
"""

import os
import time
import re
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

def setup_browser():
    """Setup browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_window_size(1366, 768)
    
    return driver

def close_all_modals(driver):
    """Close all modals aggressively"""
    print("   🚪 Closing all modals...")
    
    modal_close_attempts = [
        "//button[contains(text(), 'Not now')]",
        "//button[contains(text(), 'Not Now')]", 
        "//button[contains(text(), 'Save Info')]",
        "//button[@aria-label='Close']",
        "[role='dialog'] button[aria-label*='Close']"
    ]
    
    for selector in modal_close_attempts:
        try:
            elements = driver.find_elements(By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    element.click()
                    print(f"      ❌ Closed modal")
                    time.sleep(1)
        except:
            continue

def login_and_setup(driver):
    """Login to Instagram"""
    username = "enriaqui"
    password = "Raemarie123!"
    
    print("🔐 Logging in...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    # Accept cookies
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
        )
        accept_btn.click()
        time.sleep(2)
    except:
        pass
    
    # Login
    username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    password_field = driver.find_element(By.NAME, "password")
    
    username_field.send_keys(username)
    password_field.send_keys(password)
    
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_btn.click()
    time.sleep(8)
    
    # Close post-login modals
    close_all_modals(driver)
    
    # Navigate to post
    url = "https://www.instagram.com/p/C0xFHGOrBN7/"
    print(f"\\n🔍 Loading post: {url}")
    driver.get(url)
    time.sleep(6)
    
    # Close any additional modals
    close_all_modals(driver)
    
    return True

def find_visual_next_button(driver):
    """Find the small > next button on the right side"""
    print("   🔍 Looking for visual next button (small > on right)...")
    
    # Strategy 1: Look for button with specific positioning (right side)
    try:
        # Find buttons that might be the carousel navigation
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        
        # Get image container to understand positioning
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        image_location = main_image.location
        image_size = main_image.size
        
        # Calculate right edge of image
        image_right = image_location['x'] + image_size['width']
        
        for btn in buttons:
            if btn.is_displayed():
                btn_location = btn.location
                btn_size = btn.size
                
                # Check if button is positioned on the right side of the image
                if (btn_location['x'] > image_right - 100 and  # Near right edge
                    btn_location['x'] < image_right + 50 and   # Not too far right
                    abs(btn_location['y'] - (image_location['y'] + image_size['height'] // 2)) < 100):  # Vertically centered
                    
                    # Check button size (should be small)
                    if btn_size['width'] < 60 and btn_size['height'] < 60:
                        print(f"      🎯 Found candidate next button at ({btn_location['x']}, {btn_location['y']}) size: {btn_size}")
                        return btn
    except Exception as e:
        print(f"      ❌ Strategy 1 failed: {e}")
    
    # Strategy 2: Look for specific carousel navigation classes/attributes
    carousel_selectors = [
        "button[aria-label*='Next']",
        "button[data-testid*='next']",
        "button[data-testid*='carousel']",
        "[role='button'][aria-label*='Next']",
        "button svg[aria-label*='Next']",
        ".carousel-next",
        ".next-button"
    ]
    
    for selector in carousel_selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, selector)
            if btn.is_displayed() and btn.is_enabled():
                print(f"      ✅ Found next button with selector: {selector}")
                return btn
        except:
            continue
    
    # Strategy 3: Look for buttons containing right arrow symbols
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            if btn.is_displayed():
                btn_html = btn.get_attribute('outerHTML')
                # Look for right arrow characters or SVG paths
                if any(arrow in btn_html for arrow in ['>', '➤', '▶', 'chevron-right', 'arrow-right']):
                    print(f"      ✅ Found button with arrow symbol")
                    return btn
    except:
        pass
    
    print("      ❌ Could not find visual next button")
    return None

def extract_image_id(url):
    """Extract image ID"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)
    return None

def get_current_main_image(driver):
    """Get current main image"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if ("fbcdn.net" in src and "t51.29350-15" in src and 
            "profile_pic" not in src and img.is_displayed()):
            
            try:
                if img.size['width'] > 200:
                    return {
                        "src": src,
                        "alt": alt,
                        "image_id": extract_image_id(src)
                    }
            except:
                pass
    return None

def download_image(url: str, filepath: str, cookies=None) -> bool:
    """Download image"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    }
    
    session = requests.Session()
    if cookies:
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.instagram.com'))
    
    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = os.path.getsize(filepath)
        print(f"  ✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return size > 1000
    except Exception as e:
        print(f"  ❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def main():
    print("🎯 Targeting visual next button for carousel extraction...")
    
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    carousel_images = []
    seen_image_ids = set()
    
    try:
        # Login and setup
        if not login_and_setup(driver):
            print("❌ Failed to login")
            return
        
        # Extract images by clicking the visual next button
        for i in range(1, 6):
            print(f"\\n📸 Extracting image {i}...")
            
            # Get current image
            current_image = get_current_main_image(driver)
            if current_image and current_image["image_id"]:
                if current_image["image_id"] not in seen_image_ids:
                    carousel_images.append(current_image)
                    seen_image_ids.add(current_image["image_id"])
                    print(f"   ✅ Found image {i}: ID {current_image['image_id']}")
                    print(f"       Alt: {current_image['alt'][:70]}...")
                    
                    # Take screenshot
                    screenshot_path = os.path.join(output_dir, f"visual_carousel_{i}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot: {screenshot_path}")
                else:
                    print(f"   🔄 Same image (ID: {current_image['image_id']}) - reached end")
                    break
            else:
                print("   ❌ Could not extract current image")
                break
            
            # Look for and click next button (except on last iteration)
            if i < 5:
                next_btn = find_visual_next_button(driver)
                if next_btn:
                    try:
                        # Scroll into view
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        time.sleep(1)
                        
                        # Click the button
                        actions = ActionChains(driver)
                        actions.move_to_element(next_btn).click().perform()
                        print(f"   🖱️  Clicked visual next button")
                        
                        # Wait for navigation
                        time.sleep(4)
                    except Exception as e:
                        print(f"   ❌ Failed to click next button: {e}")
                        break
                else:
                    print(f"   🏁 No next button found - end of carousel")
                    break
        
        print(f"\\n📊 Extracted {len(carousel_images)} carousel images")
        
        # Download all images
        cookies = driver.get_cookies()
        downloaded = 0
        
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
            if download_image(img_data["src"], filepath, cookies):
                downloaded += 1
        
        # Update extraction info
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
            f.write(f"Images extracted: {downloaded}\\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Visual next button targeting\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
        
        print(f"\\n✅ Successfully extracted {downloaded} carousel images!")
        
        # Keep browser open for manual verification
        print("\\n👀 Keeping browser open for 15 seconds for verification...")
        time.sleep(15)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()