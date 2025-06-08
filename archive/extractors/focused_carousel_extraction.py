#!/usr/bin/env python3
"""
Focused carousel extraction with automatic modal handling
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
import random

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
    """Aggressively close all possible modals"""
    print("   🚪 Closing all modals...")
    
    modal_selectors = [
        "//button[contains(text(), 'Not now')]",
        "//button[contains(text(), 'Not Now')]", 
        "//button[contains(text(), 'Save Info')]",
        "//button[contains(text(), 'Turn on')]",
        "//button[contains(text(), 'Turn On')]",
        "//button[@aria-label='Close']",
        "//button[@aria-label='close']",
        "[role='dialog'] button",
        ".modal button",
        "[data-testid='modal'] button"
    ]
    
    for selector in modal_selectors:
        try:
            elements = driver.find_elements(By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    element.click()
                    print(f"      ❌ Closed modal with selector: {selector}")
                    time.sleep(1)
        except:
            continue
    
    # Additional attempts to close any remaining modals
    try:
        # Look for any visible dialogs
        dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
        for dialog in dialogs:
            if dialog.is_displayed():
                # Try to find close buttons within the dialog
                close_buttons = dialog.find_elements(By.CSS_SELECTOR, "button")
                for btn in close_buttons:
                    btn_text = btn.text.lower()
                    if any(word in btn_text for word in ['not now', 'close', 'cancel', 'skip']):
                        btn.click()
                        print(f"      ❌ Closed dialog with button: {btn.text}")
                        time.sleep(1)
                        break
    except:
        pass

def login_and_navigate(driver):
    """Login and navigate to post with modal handling"""
    username = "enriaqui"
    password = "Raemarie123!"
    
    print("🔐 Logging in to Instagram...")
    
    # Login
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    # Accept cookies
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
        )
        accept_btn.click()
        print("   🍪 Accepted cookies")
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
    print("   📧 Submitted login")
    
    time.sleep(8)
    
    # Close post-login modals aggressively
    close_all_modals(driver)
    
    # Navigate to post
    url = "https://www.instagram.com/p/C0xFHGOrBN7/"
    print(f"\\n🔍 Loading post: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Close any modals that might appear on the post page
    close_all_modals(driver)
    
    return True

def extract_image_id(url):
    """Extract image ID"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)
    return None

def get_current_main_image(driver):
    """Get the main image currently displayed"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if ("fbcdn.net" in src and "t51.29350-15" in src and 
            "profile_pic" not in src and img.is_displayed()):
            
            # Prefer larger images
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

def navigate_next(driver):
    """Try to navigate to next image"""
    print("   🎯 Trying to navigate to next image...")
    
    # Method 1: Find Next button
    try:
        # Look for various Next button patterns
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='next']", 
            "[role='button'][aria-label*='Next']",
            "[role='button'][aria-label*='next']"
        ]
        
        for selector in next_selectors:
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if next_btn.is_displayed() and next_btn.is_enabled():
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(1)
                    
                    # Click
                    actions = ActionChains(driver)
                    actions.move_to_element(next_btn).click().perform()
                    print(f"      ✅ Clicked Next button: {selector}")
                    time.sleep(3)
                    return True
            except:
                continue
    except:
        pass
    
    # Method 2: Keyboard navigation
    try:
        print("      ⌨️  Trying keyboard navigation...")
        # Click on image first to focus
        main_img = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        actions = ActionChains(driver)
        actions.move_to_element(main_img).click().perform()
        time.sleep(1)
        
        # Press right arrow
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        print("      ⌨️  Pressed right arrow")
        time.sleep(3)
        return True
    except:
        pass
    
    print("      ❌ No navigation method worked")
    return False

def download_image(url: str, filepath: str, cookies=None) -> bool:
    """Download image"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
    print("🎯 Focused carousel extraction for C0xFHGOrBN7...")
    
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    carousel_images = []
    seen_image_ids = set()
    
    try:
        # Login and navigate
        if not login_and_navigate(driver):
            print("❌ Failed to login and navigate")
            return
        
        # Extract images by navigating through carousel
        for i in range(1, 6):  # Try to get up to 5 images
            print(f"\\n📸 Extracting image {i}...")
            
            current_image = get_current_main_image(driver)
            if current_image and current_image["image_id"]:
                if current_image["image_id"] not in seen_image_ids:
                    carousel_images.append(current_image)
                    seen_image_ids.add(current_image["image_id"])
                    print(f"   ✅ Found image {i}: ID {current_image['image_id']}, Alt: {current_image['alt'][:50]}...")
                    
                    # Take screenshot
                    screenshot_path = os.path.join(output_dir, f"carousel_image_{i}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot: {screenshot_path}")
                else:
                    print(f"   🔄 Same image as before (ID: {current_image['image_id']}) - end of carousel")
                    break
            else:
                print("   ❌ Could not extract current image")
                break
            
            # Try to navigate to next (except for last iteration)
            if i < 5:
                if not navigate_next(driver):
                    print(f"   🏁 Cannot navigate further - end of carousel")
                    break
        
        print(f"\\n📊 Found {len(carousel_images)} total carousel images")
        
        # Download images
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
            f.write(f"Method: Focused carousel navigation with modal handling\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
        
        print(f"\\n✅ Extraction complete: {downloaded} images downloaded")
        
        # Keep browser open briefly for verification
        print("\\n👀 Keeping browser open for 10 seconds...")
        time.sleep(10)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()