#!/usr/bin/env python3
"""
Comprehensive carousel extractor with all strategies to get 3 unique images
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
    """Setup browser with maximum realism"""
    options = Options()
    
    # Use most common user agent
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Anti-detection
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Realistic preferences
    prefs = {
        "profile.default_content_setting_values": {"notifications": 2}
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Hide automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    
    # Set realistic window size
    driver.set_window_size(1366, 768)
    
    return driver

def human_delay():
    """Random human-like delay"""
    time.sleep(random.uniform(1.5, 3.5))

def human_type(element, text):
    """Type like a human"""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.08, 0.15))

def close_all_modals(driver):
    """Aggressively close all modals"""
    print("   🚪 Closing all modals...")
    
    # List of possible modal close patterns
    close_patterns = [
        ("xpath", "//button[contains(text(), 'Not now')]"),
        ("xpath", "//button[contains(text(), 'Not Now')]"),
        ("xpath", "//button[contains(text(), 'Save Info')]"),
        ("xpath", "//button[contains(text(), 'Turn On')]"),
        ("xpath", "//button[@aria-label='Close']"),
        ("css", "[role='dialog'] button"),
        ("css", "button[aria-label*='Close']"),
        ("css", "button[aria-label*='close']"),
        ("css", ".modal button"),
        ("xpath", "//div[@role='dialog']//button")
    ]
    
    attempts = 0
    while attempts < 5:  # Try multiple rounds
        closed_any = False
        
        for method, selector in close_patterns:
            try:
                if method == "xpath":
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        try:
                            element.click()
                            print(f"      ❌ Closed modal with {method}: {selector}")
                            closed_any = True
                            time.sleep(1)
                        except:
                            pass
            except:
                continue
        
        if not closed_any:
            break
            
        attempts += 1
        time.sleep(1)

def login_to_instagram(driver):
    """Login with maximum human-like behavior"""
    username = "enriaqui"
    password = "Raemarie123!"
    
    print("🔐 Logging in to Instagram...")
    
    # Navigate to login
    driver.get("https://www.instagram.com/accounts/login/")
    human_delay()
    
    # Handle cookie consent
    try:
        accept_btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
        )
        accept_btn.click()
        print("   🍪 Accepted cookies")
        human_delay()
    except:
        print("   🍪 No cookie popup")
    
    # Wait for and fill login form
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Human-like typing
        human_type(username_field, username)
        time.sleep(random.uniform(0.8, 1.5))
        
        human_type(password_field, password)
        time.sleep(random.uniform(0.8, 1.5))
        
        # Submit
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        print("   📧 Submitted login")
        
        # Wait for login to process
        time.sleep(8)
        
        # Handle post-login modals
        close_all_modals(driver)
        
        print("   ✅ Login completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
        return False

def extract_image_id(url):
    """Extract unique image ID"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)
    return None

def get_current_main_image(driver):
    """Get the main image currently displayed"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    best_candidate = None
    best_score = 0
    
    for img in images:
        try:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if ("fbcdn.net" in src and "t51.29350-15" in src and 
                "profile_pic" not in src and img.is_displayed()):
                
                score = 0
                
                # Size scoring
                size = img.size
                if size['width'] > 400:
                    score += 100
                elif size['width'] > 200:
                    score += 50
                
                # Quality indicators
                if "1440x" in src:
                    score += 80
                elif "1080x" in src:
                    score += 60
                elif "640x" in src:
                    score += 40
                
                # Content indicators
                if "Fanthasia" in alt:
                    score += 30
                
                if score > best_score:
                    best_candidate = {
                        "src": src,
                        "alt": alt,
                        "image_id": extract_image_id(src),
                        "score": score
                    }
                    best_score = score
        except:
            continue
    
    return best_candidate

def find_and_click_next_button(driver):
    """Comprehensive next button finding and clicking"""
    print("   🎯 Looking for Next button...")
    
    # Strategy 1: Aria-label based
    next_selectors = [
        "button[aria-label*='Next']",
        "button[aria-label*='next']",
        "[role='button'][aria-label*='Next']",
        "[role='button'][aria-label*='next']"
    ]
    
    for selector in next_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(1)
                    
                    # Try multiple click methods
                    for method in ["action_click", "js_click", "direct_click"]:
                        try:
                            if method == "action_click":
                                actions = ActionChains(driver)
                                actions.move_to_element(btn).pause(0.5).click().perform()
                            elif method == "js_click":
                                driver.execute_script("arguments[0].click();", btn)
                            else:
                                btn.click()
                            
                            print(f"      ✅ Clicked Next button using {method}")
                            time.sleep(4)  # Wait for navigation
                            return True
                        except:
                            continue
        except:
            continue
    
    # Strategy 2: Position-based (right side of image)
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        image_rect = main_image.rect
        
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            if btn.is_displayed():
                btn_rect = btn.rect
                
                # Check if button is on the right side of the image
                if (btn_rect['x'] > image_rect['x'] + image_rect['width'] - 100 and
                    btn_rect['y'] > image_rect['y'] and
                    btn_rect['y'] < image_rect['y'] + image_rect['height'] and
                    btn_rect['width'] < 80 and btn_rect['height'] < 80):
                    
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element(btn).pause(0.5).click().perform()
                        print(f"      ✅ Clicked position-based Next button")
                        time.sleep(4)
                        return True
                    except:
                        continue
    except:
        pass
    
    # Strategy 3: Keyboard navigation
    try:
        print("      ⌨️  Trying keyboard navigation...")
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        # Click on image to focus
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click().perform()
        time.sleep(1)
        
        # Try right arrow
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        print("      ⌨️  Pressed right arrow")
        time.sleep(4)
        return True
    except:
        pass
    
    print("      ❌ No navigation method worked")
    return False

def download_image(url: str, filepath: str, cookies=None) -> bool:
    """Download image with session cookies"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
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
    print("🎯 Comprehensive carousel extraction - aiming for all 3 images!")
    
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    carousel_images = []
    seen_image_ids = set()
    
    try:
        # Step 1: Login
        if not login_to_instagram(driver):
            print("❌ Login failed")
            return
        
        # Step 2: Navigate to post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"\\n🔍 Loading post: {url}")
        driver.get(url)
        human_delay()
        
        # Close any additional modals on post page
        close_all_modals(driver)
        
        # Wait for full page load
        time.sleep(5)
        
        # Step 3: Extract carousel images
        for attempt in range(1, 8):  # Try up to 7 times to get all images
            print(f"\\n📸 Extraction attempt {attempt}...")
            
            # Get current image
            current_image = get_current_main_image(driver)
            if current_image and current_image["image_id"]:
                if current_image["image_id"] not in seen_image_ids:
                    carousel_images.append(current_image)
                    seen_image_ids.add(current_image["image_id"])
                    print(f"   ✅ NEW IMAGE FOUND!")
                    print(f"       Image {len(carousel_images)}: ID {current_image['image_id']}")
                    print(f"       Alt: {current_image['alt'][:60]}...")
                    print(f"       Score: {current_image['score']}")
                    
                    # Take screenshot for verification
                    screenshot_path = os.path.join(output_dir, f"carousel_step_{attempt}_image_{len(carousel_images)}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot: {screenshot_path}")
                    
                    # If we have 3 images, we're done!
                    if len(carousel_images) >= 3:
                        print("   🎉 SUCCESS! Found 3 images!")
                        break
                else:
                    print(f"   🔄 Same image as before (ID: {current_image['image_id']})")
                    
                    # If we've seen this image before and have some images, try one more navigation
                    if len(carousel_images) > 0:
                        print("   🔄 Trying additional navigation...")
                        if not find_and_click_next_button(driver):
                            print("   🏁 No more navigation possible - stopping")
                            break
                    else:
                        print("   🏁 Still on first image - stopping")
                        break
            else:
                print("   ❌ Could not extract current image")
                break
            
            # Try to navigate to next image (except on last possible attempt)
            if attempt < 7 and len(carousel_images) < 3:
                success = find_and_click_next_button(driver)
                if not success:
                    print(f"   🏁 Navigation failed - ending extraction")
                    break
                    
                # Extra wait after navigation
                time.sleep(2)
        
        # Summary
        print(f"\\n📊 EXTRACTION COMPLETE!")
        print(f"   Found {len(carousel_images)} unique carousel images")
        
        for i, img in enumerate(carousel_images, 1):
            print(f"   {i}. ID: {img['image_id']}, Alt: {img['alt'][:50]}...")
        
        # Step 4: Download all images
        cookies = driver.get_cookies()
        downloaded = 0
        
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
            if download_image(img_data["src"], filepath, cookies):
                downloaded += 1
        
        # Step 5: Create extraction summary
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
            f.write(f"Images extracted: {downloaded}\\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Comprehensive multi-strategy carousel extraction\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
                f.write(f"   Score: {img_data['score']}\\n")
        
        final_message = f"🎯 FINAL RESULT: {downloaded} images successfully extracted and downloaded!"
        if downloaded >= 3:
            final_message += " 🎉 ALL 3 IMAGES ACHIEVED!"
        print(f"\\n{final_message}")
        
        # Keep browser open for verification
        print("\\n👀 Keeping browser open for 15 seconds for manual verification...")
        time.sleep(15)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()