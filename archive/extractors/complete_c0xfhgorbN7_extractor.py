#!/usr/bin/env python3
"""
Complete C0xFHGOrBN7 Extractor - Get all 3 carousel images using multiple strategies
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import json

def setup_browser():
    """Setup browser with anti-detection"""
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

def download_image(url: str, filepath: str, headers: dict) -> bool:
    """Download image with proper headers"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = os.path.getsize(filepath)
        print(f"    ✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return size > 5000  # Valid image should be larger than 5KB
        
    except Exception as e:
        print(f"    ❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def close_popups(driver):
    """Close all popups and modals"""
    print("  🚪 Closing popups...")
    
    popup_selectors = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow')]",
        "//button[contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Not now')]",
        "//button[@aria-label='Close']",
        "//button[contains(@aria-label, 'Close')]",
        "//button[contains(text(), 'Save')]",
        "//button[contains(text(), 'Turn On')]",
        "//div[@role='dialog']//button"
    ]
    
    for selector in popup_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"    ❌ Closed popup")
                    time.sleep(1)
                    break
        except:
            continue

def strategy_1_direct_navigation(driver, shortcode, output_dir):
    """Strategy 1: Direct carousel navigation with Next button clicking"""
    print("\n🎯 Strategy 1: Manual carousel navigation")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(5)
    
    close_popups(driver)
    time.sleep(3)
    
    images_downloaded = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Try to find carousel images by clicking Next button
    for position in range(1, 4):  # Try positions 1, 2, 3
        print(f"  📍 Getting image at position {position}")
        
        # Wait a bit for images to load
        time.sleep(2)
        
        # Find all high-quality images
        img_selectors = [
            "article img[src*='1440x']",
            "article img[src*='1080x']", 
            "article img[src*='t51.29350-15']",
            "main img[src*='1440x']",
            "main img[src*='1080x']",
            "main img[src*='t51.29350-15']"
        ]
        
        main_image_src = None
        for selector in img_selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    src = img.get_attribute('src')
                    if src and not any(exclude in src for exclude in ['profile', 'avatar', 's150x150', 's320x320']):
                        main_image_src = src
                        break
                if main_image_src:
                    break
            except:
                continue
        
        if main_image_src and main_image_src not in [img[0] for img in images_downloaded]:
            filename = f"C0xFHGOrBN7_strategy1_pos{position}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            if download_image(main_image_src, filepath, headers):
                images_downloaded.append((main_image_src, position))
        
        # Try to click Next button for next image
        if position < 3:
            next_selectors = [
                "button[aria-label*='Next']",
                "button[aria-label*='next']", 
                "[aria-label*='Next']",
                "[aria-label*='Go to slide']",
                ".carousel button:last-child",
                "button:has(svg[aria-label*='Next'])"
            ]
            
            clicked_next = False
            for selector in next_selectors:
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        ActionChains(driver).move_to_element(next_btn).click().perform()
                        print(f"    ➡️ Clicked Next button")
                        time.sleep(2)
                        clicked_next = True
                        break
                except:
                    continue
            
            if not clicked_next:
                print(f"    ⚠️ Could not find Next button")
    
    print(f"  📊 Strategy 1 downloaded: {len(images_downloaded)} images")
    return images_downloaded

def strategy_2_url_variations(driver, shortcode, output_dir):
    """Strategy 2: Try different URL patterns and parameters"""
    print("\n🎯 Strategy 2: URL variations")
    
    images_downloaded = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Try different URL patterns
    url_patterns = [
        f"https://www.instagram.com/p/{shortcode}/",
        f"https://www.instagram.com/p/{shortcode}/?img_index=1",
        f"https://www.instagram.com/p/{shortcode}/?img_index=2", 
        f"https://www.instagram.com/p/{shortcode}/?img_index=3",
        f"https://www.instagram.com/p/{shortcode}/?taken-by=",
        f"https://www.instagram.com/p/{shortcode}/?hl=en"
    ]
    
    for i, url in enumerate(url_patterns):
        print(f"  🔗 Trying URL variation {i+1}: {url}")
        
        try:
            driver.get(url)
            time.sleep(4)
            
            if i == 0:  # Only close popups on first load
                close_popups(driver)
                time.sleep(2)
            
            # Find main content images
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
            
            for img in img_elements:
                src = img.get_attribute('src')
                if (src and 't51.29350-15' in src and 
                    not any(exclude in src for exclude in ['profile', 'avatar', 's150x150', 's320x320']) and
                    src not in [img[0] for img in images_downloaded]):
                    
                    filename = f"C0xFHGOrBN7_strategy2_var{i+1}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    if download_image(src, filepath, headers):
                        images_downloaded.append((src, i+1))
                        break
                        
        except Exception as e:
            print(f"    ⚠️ URL variation {i+1} failed: {e}")
    
    print(f"  📊 Strategy 2 downloaded: {len(images_downloaded)} images")
    return images_downloaded

def strategy_3_aggressive_scraping(driver, shortcode, output_dir):
    """Strategy 3: Aggressive scraping with all possible selectors"""
    print("\n🎯 Strategy 3: Aggressive scraping")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)  # Longer wait
    
    close_popups(driver)
    time.sleep(3)
    
    # Execute JavaScript to load more content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    images_downloaded = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    # Try every possible image selector
    selectors = [
        "article img",
        "main img", 
        "[role='main'] img",
        "div[style*='padding-bottom'] img",
        "img[src*='t51.29350-15']",
        "img[src*='1440x']",
        "img[src*='1080x']",
        "img[src*='scontent']",
        "img[srcset*='1440w']",
        "*[style*='background-image']"  # Also check background images
    ]
    
    all_unique_urls = set()
    
    for selector in selectors:
        try:
            if 'background-image' in selector:
                # Handle background images
                elements = driver.find_elements(By.CSS_SELECTOR, selector.replace("*[style*='background-image']", "*"))
                for elem in elements:
                    style = elem.get_attribute('style') or ''
                    if 'background-image' in style:
                        # Extract URL from background-image CSS
                        import re
                        urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
                        for url in urls:
                            if 'instagram' in url and 't51.29350-15' in url:
                                all_unique_urls.add(url)
            else:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    src = img.get_attribute('src')
                    if (src and 't51.29350-15' in src and 
                        not any(exclude in src for exclude in ['profile', 'avatar', 's150x150', 's320x320'])):
                        all_unique_urls.add(src)
                        
                    # Also check srcset
                    srcset = img.get_attribute('srcset')
                    if srcset:
                        import re
                        urls = re.findall(r'(https://[^\s]+)', srcset)
                        for url in urls:
                            if 'instagram' in url and 't51.29350-15' in url:
                                all_unique_urls.add(url)
        except:
            continue
    
    print(f"  📊 Found {len(all_unique_urls)} unique image URLs")
    
    # Download all unique images
    for i, src in enumerate(sorted(all_unique_urls), 1):
        filename = f"C0xFHGOrBN7_strategy3_img{i}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        if download_image(src, filepath, headers):
            images_downloaded.append((src, i))
    
    print(f"  📊 Strategy 3 downloaded: {len(images_downloaded)} images")
    return images_downloaded

def main():
    """Run all strategies to get complete carousel"""
    print("🎯 COMPLETE C0xFHGOrBN7 CAROUSEL EXTRACTION")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Clean output directory
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith(('.jpg', '.png', '.jpeg')):
                os.remove(os.path.join(output_dir, file))
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    
    try:
        # Run all strategies
        strategy1_results = strategy_1_direct_navigation(driver, shortcode, output_dir)
        strategy2_results = strategy_2_url_variations(driver, shortcode, output_dir)
        strategy3_results = strategy_3_aggressive_scraping(driver, shortcode, output_dir)
        
        # Combine and deduplicate results
        all_urls = set()
        all_results = []
        
        for results in [strategy1_results, strategy2_results, strategy3_results]:
            for url, info in results:
                if url not in all_urls:
                    all_urls.add(url)
                    all_results.append((url, info))
        
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Total unique images found: {len(all_results)}")
        print(f"🎯 Target: 3 images")
        
        # Save extraction summary
        summary_path = os.path.join(output_dir, "extraction_summary.json")
        summary = {
            "shortcode": shortcode,
            "target_images": 3,
            "extracted_images": len(all_results),
            "strategies_used": 3,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "image_urls": [url for url, _ in all_results]
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # List downloaded files
        downloaded_files = [f for f in os.listdir(output_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        print(f"\n📁 Downloaded files:")
        for file in sorted(downloaded_files):
            filepath = os.path.join(output_dir, file)
            size = os.path.getsize(filepath)
            print(f"  ✅ {file} ({size} bytes)")
        
        success = len(downloaded_files) >= 3
        print(f"\n{'🎊 SUCCESS' if success else '⚠️ PARTIAL'}: {len(downloaded_files)}/3 images extracted")
        
        return success
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()