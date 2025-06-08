#!/usr/bin/env python3
"""
Aggressive carousel extraction with multiple strategies and longer waits
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
    """Setup browser with realistic user behavior"""
    options = Options()
    
    # Use realistic user agent
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Anti-detection settings
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

def human_like_type(element, text, delay_range=(0.05, 0.15)):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(*delay_range))

def login_to_instagram(driver, username, password):
    """Login to Instagram"""
    print("🔐 Logging in to Instagram...")
    
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(random.uniform(3, 5))
    
    try:
        # Handle cookie consent
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
            )
            accept_btn.click()
            print("   🍪 Accepted cookies")
            time.sleep(2)
        except:
            print("   🍪 No cookie popup")
        
        # Login
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.clear()
        human_like_type(username_field, username)
        time.sleep(random.uniform(0.5, 1.0))
        
        password_field.clear()
        human_like_type(password_field, password)
        time.sleep(random.uniform(0.5, 1.0))
        
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        print("   📧 Submitted login form")
        time.sleep(8)
        
        # Handle post-login popups
        try:
            not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
            not_now_btn.click()
            print("   💾 Dismissed save login info")
            time.sleep(2)
        except:
            pass
        
        try:
            not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
            not_now_btn.click()
            print("   🔔 Dismissed notifications")
            time.sleep(2)
        except:
            pass
        
        print("   ✅ Login successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False

def extract_image_id(url):
    """Extract the unique image ID from Instagram URL"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)
    return None

def get_all_carousel_images(driver):
    """Get all images from current view and analyze them"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    carousel_candidates = []
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if "fbcdn.net" in src and "t51.29350-15" in src and "profile_pic" not in src:
            image_id = extract_image_id(src)
            if image_id:
                carousel_candidates.append({
                    "src": src,
                    "alt": alt,
                    "image_id": image_id,
                    "element": img
                })
    
    print(f"   📊 Found {len(carousel_candidates)} potential carousel images:")
    for i, img in enumerate(carousel_candidates):
        print(f"      {i+1}. ID: {img['image_id']}, Alt: {img['alt'][:50]}...")
    
    return carousel_candidates

def try_all_navigation_methods(driver):
    """Try every possible method to navigate to next image"""
    print("   🎯 Trying all possible navigation methods...")
    
    methods_tried = []
    
    # Method 1: Click Next button with aria-label
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
        if next_btn.is_displayed() and next_btn.is_enabled():
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(1)
            actions = ActionChains(driver)
            actions.move_to_element(next_btn).click().perform()
            methods_tried.append("aria-label Next button")
            time.sleep(4)  # Longer wait
    except:
        pass
    
    # Method 2: Search all buttons for Next
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            aria_label = btn.get_attribute("aria-label") or ""
            if "next" in aria_label.lower() and btn.is_displayed():
                actions = ActionChains(driver)
                actions.move_to_element(btn).click().perform()
                methods_tried.append(f"button search: {aria_label}")
                time.sleep(4)
                break
    except:
        pass
    
    # Method 3: Right arrow key
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click().send_keys(Keys.ARROW_RIGHT).perform()
        methods_tried.append("right arrow key")
        time.sleep(4)
    except:
        pass
    
    # Method 4: Swipe simulation
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click_and_hold().move_by_offset(-200, 0).release().perform()
        methods_tried.append("swipe left simulation")
        time.sleep(4)
    except:
        pass
    
    # Method 5: Space key
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        actions = ActionChains(driver)
        actions.click(body).send_keys(Keys.SPACE).perform()
        methods_tried.append("space key")
        time.sleep(4)
    except:
        pass
    
    print(f"      Tried methods: {', '.join(methods_tried)}")
    return len(methods_tried) > 0

def download_image(url: str, filepath: str, cookies=None) -> bool:
    """Download image with proper headers"""
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
    print("🔍 Aggressive carousel extraction for C0xFHGOrBN7...")
    
    username = "enriaqui"
    password = "Raemarie123!"
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    all_found_images = {}  # Dictionary to store all unique images found
    
    try:
        # Login
        if not login_to_instagram(driver, username, password):
            print("❌ Login failed")
            return
        
        # Navigate to post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"\\n🔍 Loading post: {url}")
        driver.get(url)
        time.sleep(10)  # Longer initial wait
        
        # Take screenshot for analysis
        screenshot_path = os.path.join(output_dir, "initial_post_view.png")
        driver.save_screenshot(screenshot_path)
        print(f"   📸 Initial screenshot: {screenshot_path}")
        
        # Extract all initial images
        print("\\n📸 Analyzing initial view...")
        initial_images = get_all_carousel_images(driver)
        
        for img in initial_images:
            if img["image_id"] not in all_found_images:
                all_found_images[img["image_id"]] = img
        
        # Try navigation multiple times with different methods
        for attempt in range(1, 6):
            print(f"\\n🎯 Navigation attempt {attempt}...")
            
            # Try navigation
            if try_all_navigation_methods(driver):
                # Wait longer for potential changes
                time.sleep(6)
                
                # Take screenshot after navigation
                screenshot_after = os.path.join(output_dir, f"after_navigation_{attempt}.png")
                driver.save_screenshot(screenshot_after)
                print(f"   📸 Post-navigation screenshot: {screenshot_after}")
                
                # Check for new images
                current_images = get_all_carousel_images(driver)
                
                new_images_found = 0
                for img in current_images:
                    if img["image_id"] not in all_found_images:
                        all_found_images[img["image_id"]] = img
                        new_images_found += 1
                        print(f"   🆕 Found NEW image: ID {img['image_id']}, Alt: {img['alt'][:50]}...")
                
                if new_images_found == 0:
                    print(f"   🔄 No new images found in attempt {attempt}")
                else:
                    print(f"   ✅ Found {new_images_found} new images!")
            else:
                print(f"   ❌ No navigation methods worked in attempt {attempt}")
                break
        
        # Summary of all found images
        unique_images = list(all_found_images.values())
        print(f"\\n📊 FINAL SUMMARY: Found {len(unique_images)} total unique images")
        
        for i, img in enumerate(unique_images, 1):
            print(f"   {i}. ID: {img['image_id']}, Alt: {img['alt'][:50]}...")
        
        # Download all unique images
        cookies = driver.get_cookies()
        downloaded = 0
        
        for i, img_data in enumerate(unique_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(unique_images)}...")
            if download_image(img_data["src"], filepath, cookies):
                downloaded += 1
            
            time.sleep(1)
        
        # Update extraction info
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
            f.write(f"Images extracted: {downloaded}\\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Aggressive multi-method carousel navigation\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(unique_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
        
        print(f"\\n✅ Aggressive extraction complete: {downloaded} images downloaded")
        
        # Keep browser open for manual inspection
        print("\\n👀 Keeping browser open for 20 seconds for manual verification...")
        time.sleep(20)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()