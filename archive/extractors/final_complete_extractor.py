#!/usr/bin/env python3
"""
Final complete extractor - handles all popups including Google password save
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
    
    # Disable password save prompts from Chrome/Google
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2
        },
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False,
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)
    
    # Additional flags to disable password manager
    options.add_argument("--disable-password-generation")
    options.add_argument("--disable-password-manager-reauthentication")
    options.add_argument("--disable-save-password-bubble")
    
    # Anti-detection
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Hide automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_window_size(1366, 768)
    
    return driver

def close_all_popups_and_modals(driver):
    """Close all possible popups including Google password save"""
    print("   🚪 Closing all popups and modals...")
    
    # Extended list including Google password save patterns
    close_patterns = [
        ("xpath", "//button[contains(text(), 'Not now')]"),
        ("xpath", "//button[contains(text(), 'Not Now')]"),
        ("xpath", "//button[contains(text(), 'Never')]"),
        ("xpath", "//button[contains(text(), 'No Thanks')]"),
        ("xpath", "//button[contains(text(), 'No thanks')]"),
        ("xpath", "//button[contains(text(), 'Save Info')]"),
        ("xpath", "//button[contains(text(), 'Turn On')]"),
        ("xpath", "//button[@aria-label='Close']"),
        ("xpath", "//button[@aria-label='close']"),
        ("css", "[role='dialog'] button"),
        ("css", "button[aria-label*='Close']"),
        ("css", "button[aria-label*='close']"),
        ("css", ".modal button"),
        ("xpath", "//div[@role='dialog']//button"),
        # Google password save specific
        ("xpath", "//button[contains(text(), 'Never for this site')]"),
        ("xpath", "//button[contains(text(), 'Nope')]"),
        ("css", "[data-value='never']"),
        ("css", "button[data-dismiss]")
    ]
    
    attempts = 0
    while attempts < 8:  # More attempts
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
                            print(f"      ❌ Closed popup: {selector}")
                            closed_any = True
                            time.sleep(1.5)
                        except:
                            pass
            except:
                continue
        
        # Also try pressing Escape key to close popups
        try:
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
        
        if not closed_any:
            break
            
        attempts += 1
        time.sleep(1)

def login_to_instagram(driver):
    """Login with enhanced popup handling"""
    username = "enriaqui"
    password = "Raemarie123!"
    
    print("🔐 Logging in to Instagram...")
    
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    # Accept cookies
    try:
        accept_btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
        )
        accept_btn.click()
        print("   🍪 Accepted cookies")
        time.sleep(2)
    except:
        pass
    
    # Login
    try:
        username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)
        
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)
        
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        print("   📧 Submitted login")
        
        # Wait for login to process
        time.sleep(10)
        
        # Close all popups including Google password save
        close_all_popups_and_modals(driver)
        
        print("   ✅ Login completed and popups closed")
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

def navigate_carousel(driver):
    """Try all navigation methods"""
    print("   🎯 Navigating carousel...")
    
    # Method 1: Click Next button
    try:
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='next']",
            "[role='button'][aria-label*='Next']"
        ]
        
        for selector in next_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        
                        # Try action click
                        actions = ActionChains(driver)
                        actions.move_to_element(btn).pause(0.8).click().perform()
                        print(f"      ✅ Clicked Next button")
                        time.sleep(5)  # Longer wait
                        return True
            except:
                continue
    except:
        pass
    
    # Method 2: Keyboard navigation
    try:
        print("      ⌨️  Trying keyboard navigation...")
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click().perform()
        time.sleep(1)
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        print("      ⌨️  Pressed right arrow")
        time.sleep(5)
        return True
    except:
        pass
    
    # Method 3: Swipe simulation
    try:
        print("      👆 Trying swipe simulation...")
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click_and_hold().move_by_offset(-300, 0).release().perform()
        print("      👆 Simulated swipe left")
        time.sleep(5)
        return True
    except:
        pass
    
    print("      ❌ All navigation methods failed")
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
            try:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.instagram.com'))
            except:
                continue
    
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
    print("🎯 FINAL COMPLETE EXTRACTION - Getting all 3 carousel images!")
    
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    carousel_images = []
    seen_image_ids = set()
    
    try:
        # Login
        if not login_to_instagram(driver):
            print("❌ Login failed")
            return
        
        # Navigate to post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"\\n🔍 Loading post: {url}")
        driver.get(url)
        time.sleep(4)
        
        # Close any popups on post page
        close_all_popups_and_modals(driver)
        time.sleep(3)
        
        # Extract all carousel images
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            print(f"\\n📸 Extraction attempt {attempt}...")
            
            # Get current image
            current_image = get_current_main_image(driver)
            if current_image and current_image["image_id"]:
                if current_image["image_id"] not in seen_image_ids:
                    carousel_images.append(current_image)
                    seen_image_ids.add(current_image["image_id"])
                    print(f"   🎉 NEW IMAGE FOUND!")
                    print(f"       Image {len(carousel_images)}: ID {current_image['image_id']}")
                    print(f"       Alt: {current_image['alt'][:60]}...")
                    
                    # Take screenshot
                    screenshot_path = os.path.join(output_dir, f"final_image_{len(carousel_images)}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot: {screenshot_path}")
                    
                    # Success! We have 3 images
                    if len(carousel_images) >= 3:
                        print("   🏆 SUCCESS! Found all 3 images!")
                        break
                else:
                    print(f"   🔄 Same image (ID: {current_image['image_id']})")
                    # If we've tried several times with same image, stop
                    if attempt > 3:
                        print("   🏁 Likely reached end of carousel")
                        break
            else:
                print("   ❌ Could not extract current image")
                if attempt > 2:
                    break
            
            # Try to navigate (unless we have 3 images)
            if len(carousel_images) < 3 and attempt < max_attempts:
                if not navigate_carousel(driver):
                    print("   🏁 Navigation failed - ending")
                    break
                
                # Close any popups that might have appeared
                close_all_popups_and_modals(driver)
        
        # Results
        print(f"\\n📊 EXTRACTION RESULTS:")
        print(f"   Found {len(carousel_images)} unique carousel images")
        
        for i, img in enumerate(carousel_images, 1):
            print(f"   {i}. ID: {img['image_id']}, Alt: {img['alt'][:50]}...")
        
        # Download images (get cookies safely)
        try:
            cookies = driver.get_cookies()
        except:
            cookies = []
            print("   ⚠️  Could not get cookies, downloading without session")
        
        downloaded = 0
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
            if download_image(img_data["src"], filepath, cookies):
                downloaded += 1
        
        # Create summary
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
            f.write(f"Images extracted: {downloaded}\\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Final complete extraction with popup handling\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
        
        # Final message
        if downloaded >= 3:
            print(f"\\n🏆🎉 COMPLETE SUCCESS! All 3 carousel images extracted and downloaded!")
        elif downloaded >= 2:
            print(f"\\n✅ Partial success! {downloaded} images extracted (2/3)")
        else:
            print(f"\\n⚠️  Limited success: {downloaded} images extracted")
        
        print("\\n👀 Keeping browser open for 10 seconds for verification...")
        time.sleep(10)
        
    except Exception as e:
        print(f"\\n❌ Extraction error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()