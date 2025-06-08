#!/usr/bin/env python3
"""
Debug script to understand the difference between carousel images and suggested content
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    """Close Instagram popups including cookie consent and login prompts"""
    # Cookie consent
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
                    break
        except:
            continue
    
    # Login prompts
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
                    break
        except:
            continue

def analyze_page_structure():
    driver = setup_browser()
    
    try:
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        time.sleep(5)
        
        close_popups(driver)
        time.sleep(3)
        
        # Find all high-quality images
        images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        carousel_images = []
        
        for i, img in enumerate(images):
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                if src and 't51.29350-15' in src and 't51.2885-19' not in src:
                    # Get parent elements to understand context
                    parent_article = None
                    parent_div = img.find_element(By.XPATH, "./ancestor::article[1]") if img.find_elements(By.XPATH, "./ancestor::article[1]") else None
                    
                    # Get position on page
                    location = img.location
                    size = img.size
                    
                    # Check if image is in main post area vs suggested content
                    main_post_container = driver.find_elements(By.CSS_SELECTOR, "article[role='presentation'], main article")
                    is_in_main_post = False
                    
                    if main_post_container:
                        try:
                            main_container = main_post_container[0]
                            main_location = main_container.location
                            main_size = main_container.size
                            
                            # Check if image is within main container bounds
                            if (location['y'] >= main_location['y'] and 
                                location['y'] <= main_location['y'] + main_size['height']):
                                is_in_main_post = True
                        except:
                            pass
                    
                    # Try to identify carousel vs suggested by DOM structure
                    carousel_indicators = img.find_elements(By.XPATH, "./ancestor::*[contains(@class, 'carousel') or contains(@class, 'slide') or contains(@style, 'transform')]")
                    has_carousel_ancestor = len(carousel_indicators) > 0
                    
                    # Check for "More posts" or similar indicators
                    more_posts_indicators = img.find_elements(By.XPATH, "./ancestor::*[contains(text(), 'More') or contains(text(), 'Related') or contains(text(), 'Suggested')]")
                    is_suggested = len(more_posts_indicators) > 0
                    
                    carousel_images.append({
                        'index': i + 1,
                        'src': src[:80] + '...',
                        'alt': alt[:50] + '...' if len(alt) > 50 else alt,
                        'location': location,
                        'size': size,
                        'is_in_main_post': is_in_main_post,
                        'has_carousel_ancestor': has_carousel_ancestor,
                        'is_suggested': is_suggested,
                        'y_position': location['y']
                    })
            except Exception as e:
                continue
        
        # Sort by Y position to understand page layout
        carousel_images.sort(key=lambda x: x['y_position'])
        
        print(f"\n📊 Found {len(carousel_images)} high-quality images:")
        print("=" * 120)
        print(f"{'#':<3} {'Y-Pos':<6} {'Main':<5} {'Carousel':<9} {'Suggested':<9} {'Alt Text':<30} {'URL'}")
        print("=" * 120)
        
        for img in carousel_images:
            print(f"{img['index']:<3} {img['y_position']:<6} {str(img['is_in_main_post']):<5} {str(img['has_carousel_ancestor']):<9} {str(img['is_suggested']):<9} {img['alt']:<30} {img['src']}")
        
        # Identify likely carousel images (top section)
        if carousel_images:
            # Group by Y position proximity (within 200px)
            groups = []
            current_group = [carousel_images[0]]
            
            for img in carousel_images[1:]:
                if abs(img['y_position'] - current_group[-1]['y_position']) < 200:
                    current_group.append(img)
                else:
                    groups.append(current_group)
                    current_group = [img]
            
            if current_group:
                groups.append(current_group)
            
            print(f"\n🎯 Analysis:")
            print(f"   Total groups by Y position: {len(groups)}")
            
            for i, group in enumerate(groups):
                y_range = f"{min(img['y_position'] for img in group)}-{max(img['y_position'] for img in group)}"
                main_post_count = sum(1 for img in group if img['is_in_main_post'])
                print(f"   Group {i+1}: {len(group)} images at Y {y_range} ({main_post_count} in main post)")
            
            # The first group is likely the carousel
            if groups:
                likely_carousel = groups[0]
                print(f"\n✅ Likely carousel images ({len(likely_carousel)} images):")
                for img in likely_carousel:
                    print(f"   {img['index']}: {img['alt']}")
                
                print(f"\n⚠️ Likely suggested content ({len(carousel_images) - len(likely_carousel)} images):")
                for group in groups[1:]:
                    for img in group:
                        print(f"   {img['index']}: {img['alt']}")
        
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    analyze_page_structure()