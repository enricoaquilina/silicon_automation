#!/usr/bin/env python3
"""
Debug complete carousel navigation to understand why we're missing images
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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

def close_popups(driver):
    """Close Instagram popups"""
    cookie_patterns = [
        "//button[contains(text(), 'Allow all cookies')]",
        "//button[contains(text(), 'Accept all')]", 
        "//button[contains(text(), 'Accept')]"
    ]
    
    for pattern in cookie_patterns:
        try:
            elements = driver.find_elements(By.XPATH, pattern)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"   ✅ Accepted cookies")
                    time.sleep(3)
                    return
        except:
            continue
    
    login_patterns = [
        "//button[contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Not now')]",
        "//a[contains(text(), 'Not now')]"
    ]
    
    for pattern in login_patterns:
        try:
            elements = driver.find_elements(By.XPATH, pattern)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"   ✅ Dismissed login prompt")
                    time.sleep(2)
                    return
        except:
            continue

def get_carousel_images_with_position(driver):
    """Get carousel images with their positions"""
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
    
    carousel_images = []
    for i, img in enumerate(images):
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            if (src and 
                't51.29350-15' in src and 
                't51.2885-19' not in src and 
                img.is_displayed()):
                
                location = img.location
                size = img.size
                
                carousel_images.append({
                    'index': i,
                    'src': src[:60] + '...',
                    'alt': alt[:40] + '...' if len(alt) > 40 else alt,
                    'location': location,
                    'size': size,
                    'y_position': location['y'],
                    'x_position': location['x']
                })
        except:
            continue
    
    return carousel_images

def analyze_navigation_buttons(driver):
    """Analyze all possible navigation elements"""
    print("\n🔍 Analyzing navigation elements...")
    
    # All possible selectors for navigation
    selectors = [
        "button[aria-label*='Next']",
        "button[aria-label='Next']",
        "[role='button'][aria-label*='Next']",
        "div[role='button'][aria-label*='Next']",
        "[aria-label*='next']",
        "[aria-label*='Next']",
        "button[data-testid*='next']",
        ".coreSpriteRightPaginationArrow",
        "[class*='next']",
        "[class*='arrow']",
        "[class*='chevron']"
    ]
    
    found_buttons = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    aria_label = elem.get_attribute('aria-label') or ''
                    class_name = elem.get_attribute('class') or ''
                    tag_name = elem.tag_name
                    location = elem.location
                    
                    found_buttons.append({
                        'selector': selector,
                        'tag': tag_name,
                        'aria_label': aria_label,
                        'class': class_name[:50],
                        'location': location,
                        'element': elem
                    })
                    
                    print(f"   ✅ Found: {tag_name} - '{aria_label}' at {location}")
        except:
            continue
    
    return found_buttons

def try_navigation_methods(driver, button_info):
    """Try multiple navigation methods on a button"""
    button = button_info['element']
    print(f"\n🎯 Testing navigation: {button_info['aria_label']}")
    
    methods = [
        ("Direct Click", lambda: button.click()),
        ("ActionChains Click", lambda: ActionChains(driver).click(button).perform()),
        ("ActionChains Move+Click", lambda: ActionChains(driver).move_to_element(button).click().perform()),
        ("ActionChains Hover+Click", lambda: ActionChains(driver).move_to_element(button).pause(0.5).click().perform()),
        ("JavaScript Click", lambda: driver.execute_script("arguments[0].click();", button)),
        ("JavaScript Force Click", lambda: driver.execute_script("arguments[0].dispatchEvent(new Event('click', {bubbles: true}));", button))
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"   Trying: {method_name}")
            method_func()
            time.sleep(2)
            print(f"   ✅ {method_name} succeeded")
            return True
        except Exception as e:
            print(f"   ❌ {method_name} failed: {str(e)[:50]}")
            continue
    
    return False

def try_keyboard_navigation(driver):
    """Try keyboard navigation methods"""
    print(f"\n⌨️ Trying keyboard navigation...")
    
    keyboard_methods = [
        ("Arrow Right", Keys.ARROW_RIGHT),
        ("Arrow Left", Keys.ARROW_LEFT),
        ("Space", Keys.SPACE),
        ("Enter", Keys.ENTER),
        ("Tab + Enter", [Keys.TAB, Keys.ENTER])
    ]
    
    for method_name, keys in keyboard_methods:
        try:
            print(f"   Trying: {method_name}")
            if isinstance(keys, list):
                for key in keys:
                    driver.find_element(By.TAG_NAME, "body").send_keys(key)
                    time.sleep(0.5)
            else:
                driver.find_element(By.TAG_NAME, "body").send_keys(keys)
            
            time.sleep(2)
            print(f"   ✅ {method_name} sent")
            return True
        except Exception as e:
            print(f"   ❌ {method_name} failed: {str(e)[:50]}")
            continue
    
    return False

def try_swipe_navigation(driver):
    """Try swipe/drag navigation"""
    print(f"\n👆 Trying swipe navigation...")
    
    try:
        # Find the main image container
        containers = driver.find_elements(By.CSS_SELECTOR, "article, [role='main'], main")
        if containers:
            container = containers[0]
            size = container.size
            location = container.location
            
            # Calculate swipe coordinates
            start_x = location['x'] + size['width'] * 0.8  # Right side
            end_x = location['x'] + size['width'] * 0.2    # Left side
            y = location['y'] + size['height'] * 0.5       # Middle
            
            print(f"   Swiping from ({start_x}, {y}) to ({end_x}, {y})")
            
            ActionChains(driver).move_by_offset(start_x, y).click_and_hold().move_by_offset(end_x - start_x, 0).release().perform()
            time.sleep(2)
            print(f"   ✅ Swipe completed")
            return True
    except Exception as e:
        print(f"   ❌ Swipe failed: {str(e)[:50]}")
    
    return False

def debug_complete_navigation():
    driver = setup_browser()
    
    try:
        shortcode = "C0xFHGOrBN7"
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        close_popups(driver)
        time.sleep(3)
        
        print(f"\n📸 Initial state analysis...")
        initial_images = get_carousel_images_with_position(driver)
        print(f"Found {len(initial_images)} initial images:")
        
        # Group by position
        top_images = [img for img in initial_images if img['y_position'] < 500]
        print(f"   Top section (carousel): {len(top_images)} images")
        for img in top_images:
            print(f"      {img['index']}: {img['alt']} at Y={img['y_position']}")
        
        # Test all navigation methods
        all_discovered_images = set(img['src'] for img in top_images)
        navigation_attempts = 0
        max_attempts = 20
        
        while navigation_attempts < max_attempts:
            print(f"\n🔄 Navigation attempt {navigation_attempts + 1}")
            
            # Method 1: Button navigation
            buttons = analyze_navigation_buttons(driver)
            navigation_success = False
            
            for button_info in buttons:
                if 'next' in button_info['aria_label'].lower():
                    before_count = len(all_discovered_images)
                    
                    if try_navigation_methods(driver, button_info):
                        time.sleep(3)
                        
                        # Check for new images
                        current_images = get_carousel_images_with_position(driver)
                        current_top_images = [img for img in current_images if img['y_position'] < 500]
                        
                        new_images = 0
                        for img in current_top_images:
                            if img['src'] not in all_discovered_images:
                                all_discovered_images.add(img['src'])
                                new_images += 1
                                print(f"      🆕 New image: {img['alt']}")
                        
                        if new_images > 0:
                            print(f"   ✅ Found {new_images} new images via button navigation")
                            navigation_success = True
                            break
                        else:
                            print(f"   ⚠️ Button navigation didn't reveal new images")
            
            # Method 2: Keyboard navigation (if button failed)
            if not navigation_success:
                before_count = len(all_discovered_images)
                
                if try_keyboard_navigation(driver):
                    current_images = get_carousel_images_with_position(driver)
                    current_top_images = [img for img in current_images if img['y_position'] < 500]
                    
                    new_images = 0
                    for img in current_top_images:
                        if img['src'] not in all_discovered_images:
                            all_discovered_images.add(img['src'])
                            new_images += 1
                            print(f"      🆕 New image: {img['alt']}")
                    
                    if new_images > 0:
                        print(f"   ✅ Found {new_images} new images via keyboard")
                        navigation_success = True
            
            # Method 3: Swipe navigation (if others failed)
            if not navigation_success:
                before_count = len(all_discovered_images)
                
                if try_swipe_navigation(driver):
                    current_images = get_carousel_images_with_position(driver)
                    current_top_images = [img for img in current_images if img['y_position'] < 500]
                    
                    new_images = 0
                    for img in current_top_images:
                        if img['src'] not in all_discovered_images:
                            all_discovered_images.add(img['src'])
                            new_images += 1
                            print(f"      🆕 New image: {img['alt']}")
                    
                    if new_images > 0:
                        print(f"   ✅ Found {new_images} new images via swipe")
                        navigation_success = True
            
            if not navigation_success:
                print(f"   🛑 No navigation method worked, stopping")
                break
            
            navigation_attempts += 1
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Total carousel images discovered: {len(all_discovered_images)}")
        print(f"   Navigation attempts: {navigation_attempts}")
        
        # Get final state
        final_images = get_carousel_images_with_position(driver)
        final_top_images = [img for img in final_images if img['y_position'] < 500]
        
        print(f"\n📁 Final carousel images:")
        for i, img in enumerate(final_top_images, 1):
            print(f"   {i}. {img['alt']}")
        
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    debug_complete_navigation()