#!/usr/bin/env python3
"""
Ultimate carousel extractor - aggressive navigation to find all 3 images
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
    """Close all possible popups"""
    print("   🚪 Closing all popups and modals...")
    
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
        ("xpath", "//button[contains(text(), 'Never for this site')]"),
        ("xpath", "//button[contains(text(), 'Nope')]"),
        ("css", "[data-value='never']"),
        ("css", "button[data-dismiss]")
    ]
    
    attempts = 0
    while attempts < 8:
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
        
        # Also try pressing Escape key
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
        
        # Close all popups
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

def ultra_aggressive_navigation(driver, attempt_num):
    """Ultra aggressive navigation with multiple strategies"""
    print(f"   🎯 Ultra aggressive navigation (attempt {attempt_num})...")
    
    strategies = [
        # Strategy 1: Direct button click with JS
        lambda: click_next_button_js(driver),
        # Strategy 2: Keyboard navigation with focus
        lambda: keyboard_navigation_focused(driver),
        # Strategy 3: Swipe simulation with different speeds
        lambda: swipe_simulation_varied(driver),
        # Strategy 4: Direct carousel container navigation
        lambda: carousel_container_navigation(driver),
        # Strategy 5: Action chains with long pauses
        lambda: action_chains_slow(driver),
        # Strategy 6: Go backwards then forwards
        lambda: backwards_then_forwards(driver),
        # Strategy 7: Multiple rapid clicks
        lambda: rapid_click_navigation(driver),
        # Strategy 8: Touch simulation
        lambda: touch_simulation(driver)
    ]
    
    # Cycle through strategies based on attempt number
    strategy_index = (attempt_num - 1) % len(strategies)
    strategy = strategies[strategy_index]
    
    print(f"      Using strategy {strategy_index + 1}: {strategy.__name__}")
    
    try:
        result = strategy()
        if result:
            print(f"      ✅ Strategy {strategy_index + 1} succeeded!")
            return True
    except Exception as e:
        print(f"      ❌ Strategy {strategy_index + 1} failed: {e}")
    
    return False

def click_next_button_js(driver):
    """Method 1: Direct JS click on next button"""
    next_selectors = [
        "button[aria-label*='Next']",
        "button[aria-label*='next']",
        "[role='button'][aria-label*='Next']",
        "button[aria-label='Next photo']",
        "button[aria-label='Next']"
    ]
    
    for selector in next_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                if btn.is_displayed() and btn.is_enabled():
                    # Direct JS click
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(3)
                    return True
        except:
            continue
    return False

def keyboard_navigation_focused(driver):
    """Method 2: Keyboard navigation with proper focus"""
    try:
        # Find the main post container
        main_article = driver.find_element(By.CSS_SELECTOR, "article[role='presentation'], article")
        
        # Click to focus and use keyboard
        actions = ActionChains(driver)
        actions.move_to_element(main_article).click().perform()
        time.sleep(1)
        
        # Multiple right arrow presses with pauses
        for i in range(3):
            actions.send_keys(Keys.ARROW_RIGHT).perform()
            time.sleep(2)
        
        return True
    except:
        return False

def swipe_simulation_varied(driver):
    """Method 3: Swipe with varied speeds and distances"""
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        # Different swipe variations
        swipe_variations = [
            (-200, 0, 1.0),  # Short swipe, slow
            (-400, 0, 0.5),  # Long swipe, fast
            (-300, 0, 0.8),  # Medium swipe, medium speed
        ]
        
        for dx, dy, speed in swipe_variations:
            actions = ActionChains(driver)
            actions.move_to_element(main_image)
            actions.click_and_hold()
            actions.pause(speed)
            actions.move_by_offset(dx, dy)
            actions.pause(speed)
            actions.release()
            actions.perform()
            time.sleep(3)
        
        return True
    except:
        return False

def carousel_container_navigation(driver):
    """Method 4: Direct carousel container interaction"""
    try:
        # Look for carousel container
        carousel_selectors = [
            "[role='button']",
            "div[style*='transform']",
            "div[aria-label*='carousel']"
        ]
        
        for selector in carousel_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    if element.is_displayed():
                        actions = ActionChains(driver)
                        actions.move_to_element(element).click().perform()
                        time.sleep(3)
                        return True
                except:
                    continue
    except:
        pass
    return False

def action_chains_slow(driver):
    """Method 5: Action chains with very slow movements"""
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        actions = ActionChains(driver)
        actions.move_to_element(main_image)
        actions.pause(2)  # Long pause
        actions.click()
        actions.pause(2)
        actions.send_keys(Keys.ARROW_RIGHT)
        actions.pause(2)
        actions.perform()
        
        time.sleep(5)
        return True
    except:
        return False

def backwards_then_forwards(driver):
    """Method 6: Go backwards first, then forwards"""
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        actions = ActionChains(driver)
        actions.move_to_element(main_image).click().perform()
        time.sleep(1)
        
        # Go backwards first
        actions.send_keys(Keys.ARROW_LEFT).perform()
        time.sleep(3)
        
        # Then forwards twice
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        time.sleep(3)
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        time.sleep(3)
        
        return True
    except:
        return False

def rapid_click_navigation(driver):
    """Method 7: Rapid clicking on different areas"""
    try:
        # Find next button and click multiple times rapidly
        next_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Next']")
        for btn in next_buttons:
            if btn.is_displayed():
                for i in range(5):  # Rapid clicks
                    try:
                        btn.click()
                        time.sleep(0.5)
                    except:
                        break
                time.sleep(3)
                return True
    except:
        pass
    return False

def touch_simulation(driver):
    """Method 8: Touch event simulation"""
    try:
        main_image = driver.find_element(By.CSS_SELECTOR, "img[src*='instagram']")
        
        # Simulate touch events with JavaScript
        driver.execute_script("""
            var element = arguments[0];
            var rect = element.getBoundingClientRect();
            var touchStart = new TouchEvent('touchstart', {
                touches: [{
                    clientX: rect.right - 50,
                    clientY: rect.top + rect.height / 2
                }]
            });
            var touchEnd = new TouchEvent('touchend', {
                touches: []
            });
            element.dispatchEvent(touchStart);
            setTimeout(() => element.dispatchEvent(touchEnd), 100);
        """, main_image)
        
        time.sleep(3)
        return True
    except:
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
    print("🚀 ULTIMATE CAROUSEL EXTRACTOR - Finding all 3 images with aggressive navigation!")
    
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
        print(f"\n🔍 Loading post: {url}")
        driver.get(url)
        time.sleep(4)
        
        # Close any popups on post page
        close_all_popups_and_modals(driver)
        time.sleep(3)
        
        # Extract all carousel images with ultra-aggressive navigation
        max_attempts = 15  # More attempts
        consecutive_same = 0
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n📸 Ultra extraction attempt {attempt}...")
            
            # Get current image
            current_image = get_current_main_image(driver)
            if current_image and current_image["image_id"]:
                if current_image["image_id"] not in seen_image_ids:
                    carousel_images.append(current_image)
                    seen_image_ids.add(current_image["image_id"])
                    consecutive_same = 0  # Reset counter
                    print(f"   🎉 NEW IMAGE FOUND!")
                    print(f"       Image {len(carousel_images)}: ID {current_image['image_id']}")
                    print(f"       Alt: {current_image['alt'][:60]}...")
                    
                    # Take screenshot
                    screenshot_path = os.path.join(output_dir, f"ultra_image_{len(carousel_images)}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot: {screenshot_path}")
                    
                    # Success! We have 3 images
                    if len(carousel_images) >= 3:
                        print("   🏆 SUCCESS! Found all 3 images!")
                        break
                else:
                    consecutive_same += 1
                    print(f"   🔄 Same image (ID: {current_image['image_id']}) - consecutive: {consecutive_same}")
                    
                    # If we've seen the same image too many times, try more aggressive navigation
                    if consecutive_same >= 3:
                        print(f"   ⚡ Switching to ultra-aggressive mode!")
            else:
                print("   ❌ Could not extract current image")
                consecutive_same += 1
            
            # Try to navigate (unless we have 3 images)
            if len(carousel_images) < 3 and attempt < max_attempts:
                if not ultra_aggressive_navigation(driver, attempt):
                    print("   🏁 All navigation strategies failed")
                    if consecutive_same >= 5:
                        print("   🏁 Too many consecutive same images - ending")
                        break
                
                # Close any popups that might have appeared
                close_all_popups_and_modals(driver)
                
                # Random wait to simulate human behavior
                time.sleep(random.uniform(2, 4))
        
        # Results
        print(f"\n📊 ULTIMATE EXTRACTION RESULTS:")
        print(f"   Found {len(carousel_images)} unique carousel images")
        
        for i, img in enumerate(carousel_images, 1):
            print(f"   {i}. ID: {img['image_id']}, Alt: {img['alt'][:50]}...")
        
        # Download images
        try:
            cookies = driver.get_cookies()
        except:
            cookies = []
            print("   ⚠️  Could not get cookies, downloading without session")
        
        downloaded = 0
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\n📥 Downloading image {i}/{len(carousel_images)}...")
            if download_image(img_data["src"], filepath, cookies):
                downloaded += 1
        
        # Create summary
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
            f.write(f"Images extracted: {downloaded}\\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Ultimate aggressive carousel extraction\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
        
        # Final message
        if downloaded >= 3:
            print(f"\n🏆🎉 ULTIMATE SUCCESS! All 3 carousel images extracted and downloaded!")
        elif downloaded >= 2:
            print(f"\n✅ Partial success! {downloaded} images extracted")
        else:
            print(f"\n⚠️  Limited success: {downloaded} images extracted")
        
        print("\n👀 Keeping browser open for 15 seconds for verification...")
        time.sleep(15)
        
    except Exception as e:
        print(f"\n❌ Extraction error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()