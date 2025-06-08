#!/usr/bin/env python3
"""
Debug carousel navigation to understand what's happening
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
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

def get_current_images(driver):
    """Get current high-quality images"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
    urls = set()
    for img in images:
        src = img.get_attribute('src')
        if src and 't51.29350-15' in src and 't51.2885-19' not in src:
            urls.add(src)
    return urls

def close_popups(driver):
    """Close Instagram popups including cookie consent"""
    print("🚪 Closing popups and cookie consent...")
    
    # Cookie consent patterns
    popup_patterns = [
        # Cookie consent
        "//button[contains(text(), 'Allow all cookies')]",
        "//button[contains(text(), 'Accept all')]", 
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow essential and optional cookies')]",
        # Regular popups
        "//button[contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Not now')]", 
        "//button[@aria-label='Close']",
        "//button[contains(@class, 'close')]",
        "//div[@role='dialog']//button"
    ]
    
    for pattern in popup_patterns:
        try:
            elements = driver.find_elements(By.XPATH, pattern)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"   ❌ Closed popup: {pattern}")
                    time.sleep(2)
                    break
        except:
            continue

def debug_navigation():
    driver = setup_browser()
    
    try:
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Close cookie consent and other popups
        close_popups(driver)
        time.sleep(3)
        
        # Get initial state
        initial_images = get_current_images(driver)
        print(f"📊 Initial images: {len(initial_images)}")
        for i, img_url in enumerate(initial_images, 1):
            print(f"  {i}. {img_url[:80]}...")
        
        # Check if it's actually a carousel
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label='Next']",
            "[role='button'][aria-label*='Next']",
            "div[role='button'][aria-label*='Next']"
        ]
        
        print(f"\n🔍 Looking for Next buttons...")
        found_buttons = []
        for selector in next_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed():
                    aria_label = btn.get_attribute('aria-label')
                    found_buttons.append((selector, aria_label, btn))
                    print(f"  ✅ Found: {selector} - '{aria_label}'")
        
        if not found_buttons:
            print("❌ No Next buttons found - this might not be a carousel!")
            
            # Check for carousel indicators
            indicators = driver.find_elements(By.CSS_SELECTOR, "div[style*='transform'], [class*='carousel'], [class*='slide']")
            print(f"🔍 Found {len(indicators)} carousel indicators")
            
            # Maybe it's a single image post?
            all_main_images = get_current_images(driver)
            print(f"📊 This post has {len(all_main_images)} total images")
            return
        
        # Try to navigate
        for i, (selector, aria_label, btn) in enumerate(found_buttons):
            print(f"\n🎯 Attempting navigation {i+1} with: {aria_label}")
            
            before_images = get_current_images(driver)
            print(f"   📊 Before click: {len(before_images)} images")
            
            try:
                # Try ActionChains first
                ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
                print(f"   ✅ ActionChains click succeeded")
            except Exception as e:
                print(f"   ⚠️ ActionChains failed: {e}")
                try:
                    # Fallback to JavaScript
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"   ✅ JavaScript click succeeded")
                except Exception as e2:
                    print(f"   ❌ JavaScript click failed: {e2}")
                    continue
            
            time.sleep(4)  # Wait for navigation
            
            # Check if we got redirected
            current_url = driver.current_url
            if "C0xFHGOrBN7" not in current_url:
                print(f"   ⚠️ Got redirected to: {current_url}")
                driver.get(url)  # Go back
                time.sleep(3)
                continue
            
            after_images = get_current_images(driver)
            print(f"   📊 After click: {len(after_images)} images")
            
            # If no images found, wait a bit more and try different selectors
            if len(after_images) == 0:
                print(f"   ⏳ No images found, waiting and trying different selectors...")
                time.sleep(3)
                
                # Try broader image selection
                all_imgs = driver.find_elements(By.TAG_NAME, "img")
                visible_imgs = [img for img in all_imgs if img.is_displayed()]
                print(f"   📊 Total visible images after click: {len(visible_imgs)}")
                
                # Re-check with original selector
                after_images = get_current_images(driver)
                print(f"   📊 High-quality images after wait: {len(after_images)}")
            
            new_images = after_images - before_images
            disappeared_images = before_images - after_images
            
            if new_images:
                print(f"   🆕 New images appeared: {len(new_images)}")
                for img in new_images:
                    print(f"      {img[:60]}...")
            
            if disappeared_images:
                print(f"   📤 Images disappeared: {len(disappeared_images)}")
            
            if not new_images and not disappeared_images:
                print(f"   🔄 No change in images - navigation may have failed")
            
            # Try one more navigation
            if new_images and i < 2:  # Only try a few times
                continue
            else:
                break
        
        # Final summary
        final_images = get_current_images(driver)
        total_unique = initial_images | final_images
        print(f"\n📋 SUMMARY:")
        print(f"   Initial: {len(initial_images)} images")
        print(f"   Final: {len(final_images)} images") 
        print(f"   Total unique discovered: {len(total_unique)} images")
        
        if len(total_unique) > len(initial_images):
            print("✅ Navigation successfully revealed new images!")
        else:
            print("❌ Navigation did not reveal new images")
        
    finally:
        print("Waiting 5 seconds before closing...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    debug_navigation()