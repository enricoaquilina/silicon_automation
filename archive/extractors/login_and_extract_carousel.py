#!/usr/bin/env python3
"""
Login to Instagram and extract carousel images with proper user session
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
    
    # Use a current, realistic user agent
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Anti-detection settings
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add realistic browser preferences
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2
        }
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Set realistic window size
    driver.set_window_size(1366, 768)
    
    return driver

def human_like_type(element, text, delay_range=(0.05, 0.15)):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(*delay_range))

def login_to_instagram(driver, username, password):
    """Login to Instagram with human-like behavior"""
    print("🔐 Logging in to Instagram...")
    
    # Go to Instagram login page
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
        
        # Wait for login form
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Clear fields and type with human-like behavior
        username_field.clear()
        human_like_type(username_field, username)
        time.sleep(random.uniform(0.5, 1.0))
        
        password_field.clear()
        human_like_type(password_field, password)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Click login button
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        
        print("   📧 Submitted login form")
        time.sleep(random.uniform(5, 8))
        
        # Check for various login outcomes
        time.sleep(3)
        
        # Check for error messages first
        try:
            error_elements = driver.find_elements(By.CSS_SELECTOR, "[role='alert'], .error, [data-testid='login-error']")
            for error in error_elements:
                if error.is_displayed():
                    error_text = error.text
                    print(f"   ❌ Login error: {error_text}")
                    if "two-factor" in error_text.lower() or "security code" in error_text.lower():
                        print("   🔐 Two-factor authentication required!")
                        return False
                    elif "incorrect" in error_text.lower() or "password" in error_text.lower():
                        print("   🔑 Incorrect credentials")
                        return False
        except:
            pass
        
        # Check for 2FA prompt
        try:
            tfa_element = driver.find_element(By.XPATH, "//input[@aria-label='Security code' or @placeholder*='security code']")
            if tfa_element.is_displayed():
                print("   🔐 Two-factor authentication code required!")
                print("   ⏸️  Please check your phone/email for the security code")
                
                # Wait for user to enter 2FA code manually
                print("   ⌨️  Please enter the 2FA code in the browser and press Enter here when done...")
                input("   Press Enter after entering 2FA code in browser: ")
                time.sleep(3)
        except:
            pass
        
        # Check if we're now logged in
        try:
            # Look for elements that appear after successful login
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Not now')]")),  # Save login info
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Not Now')]")),  # Notifications
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/']")),  # Home link
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='app-main']")),  # Main app
                    EC.url_contains("instagram.com")  # Should redirect away from login
                )
            )
            
            # Handle "Save your login info" popup
            try:
                not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                not_now_btn.click()
                print("   💾 Dismissed save login info")
                time.sleep(2)
            except:
                pass
            
            # Handle notifications popup
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
            print(f"   ❌ Login verification failed: {e}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/login_debug.png"
                driver.save_screenshot(screenshot_path)
                print(f"   📸 Debug screenshot saved: {screenshot_path}")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False

def extract_image_id(url):
    """Extract the unique image ID from Instagram URL"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)
    return None

def get_main_image_from_current_view(driver):
    """Get the main image currently displayed in the carousel"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    best_image = None
    best_score = 0
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if "fbcdn.net" in src and "t51.29350-15" in src and "profile_pic" not in src:
            score = 0
            
            # High resolution images are preferred
            if "1440x" in src:
                score += 100
            elif "1080x" in src:
                score += 80
            elif "640x" in src:
                score += 60
            
            # Images mentioning Fanthasia are likely main content
            if "Fanthasia" in alt:
                score += 30
            
            # Check if image is actually visible
            try:
                if img.is_displayed() and img.size['width'] > 200:
                    score += 20
            except:
                pass
            
            if score > best_score:
                best_image = {
                    "src": src,
                    "alt": alt,
                    "image_id": extract_image_id(src),
                    "score": score
                }
                best_score = score
    
    return best_image

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
    print("🔍 Instagram carousel extraction with login...")
    
    # Use provided credentials
    username = "enriaqui"
    password = "Raemarie123!"
    
    print(f"📧 Using username: {username}")
    print("🔐 Password provided")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    carousel_images = []
    seen_image_ids = set()
    
    try:
        # Login first
        if not login_to_instagram(driver, username, password):
            print("❌ Login failed, cannot continue")
            return
        
        # Navigate to the post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"\\n🔍 Loading post: {url}")
        driver.get(url)
        time.sleep(random.uniform(5, 8))
        
        # Extract first image
        print("\\n📸 Extracting image 1...")
        first_image = get_main_image_from_current_view(driver)
        if first_image and first_image["image_id"]:
            carousel_images.append(first_image)
            seen_image_ids.add(first_image["image_id"])
            print(f"   ✅ Found: {first_image['alt'][:50]}... (ID: {first_image['image_id']})")
        else:
            print("   ❌ Could not extract first image")
            return
        
        # Try to navigate through carousel
        for i in range(2, 6):  # Try to get up to 5 images
            print(f"\\n📸 Looking for image {i}...")
            
            # Look for Next button with multiple strategies
            next_btn = None
            
            # Strategy 1: Look for button with "Next" aria-label
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
                if next_btn.is_displayed() and next_btn.is_enabled():
                    print("   ✅ Found Next button with aria-label")
                else:
                    next_btn = None
            except:
                pass
            
            # Strategy 2: Look for carousel navigation buttons
            if not next_btn:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, "button")
                    for btn in buttons:
                        aria_label = btn.get_attribute("aria-label") or ""
                        if "next" in aria_label.lower() and btn.is_displayed():
                            next_btn = btn
                            print("   ✅ Found Next button by searching all buttons")
                            break
                except:
                    pass
            
            # Strategy 3: Use keyboard navigation
            if not next_btn:
                print("   ⌨️  Trying keyboard navigation (Right arrow)")
                try:
                    # Click on the image area first to focus
                    main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
                    actions = ActionChains(driver)
                    actions.move_to_element(main_image).click().perform()
                    time.sleep(1)
                    
                    # Press right arrow
                    actions.send_keys(Keys.ARROW_RIGHT).perform()
                    print("   ⌨️  Pressed right arrow key")
                    time.sleep(3)
                    
                    # Check if we got a new image
                    current_image = get_main_image_from_current_view(driver)
                    if current_image and current_image["image_id"]:
                        if current_image["image_id"] not in seen_image_ids:
                            carousel_images.append(current_image)
                            seen_image_ids.add(current_image["image_id"])
                            print(f"   ✅ Found new image with keyboard: {current_image['alt'][:50]}... (ID: {current_image['image_id']})")
                            continue
                        else:
                            print(f"   🔄 Same image - reached end of carousel")
                            break
                    else:
                        print("   ❌ No new image found with keyboard")
                        break
                        
                except Exception as e:
                    print(f"   ❌ Keyboard navigation failed: {e}")
                    break
            
            # If we found a Next button, click it
            if next_btn:
                try:
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(1)
                    
                    actions = ActionChains(driver)
                    actions.move_to_element(next_btn).click().perform()
                    print("   🖱️  Clicked Next button")
                    
                    time.sleep(random.uniform(2, 4))
                    
                    # Extract new image
                    current_image = get_main_image_from_current_view(driver)
                    if current_image and current_image["image_id"]:
                        if current_image["image_id"] not in seen_image_ids:
                            carousel_images.append(current_image)
                            seen_image_ids.add(current_image["image_id"])
                            print(f"   ✅ Found new image: {current_image['alt'][:50]}... (ID: {current_image['image_id']})")
                        else:
                            print(f"   🔄 Same image - reached end of carousel")
                            break
                    else:
                        print("   ❌ Could not extract new image")
                        break
                        
                except Exception as e:
                    print(f"   ❌ Failed to click Next button: {e}")
                    break
            else:
                print("   ❌ No Next button found - end of carousel")
                break
        
        print(f"\\n📊 Found {len(carousel_images)} unique carousel images")
        
        # Get browser cookies for downloads
        cookies = driver.get_cookies()
        
        # Download the images
        downloaded = 0
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
            print(f"   ID: {img_data['image_id']}, Alt: {img_data['alt'][:50]}...")
            
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
            f.write(f"Method: Logged-in carousel navigation\\n")
            f.write(f"Username: {username}\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
                f.write(f"   Score: {img_data['score']}\\n")
        
        print(f"\\n✅ Successfully extracted and downloaded {downloaded} carousel images with login")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()