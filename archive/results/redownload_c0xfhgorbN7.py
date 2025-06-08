#!/usr/bin/env python3
"""
Re-download all 3 images for C0xFHGOrBN7 using fresh URLs from browser
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

def setup_browser():
    """Setup Chrome browser with stealth configuration"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def download_image(url: str, filepath: str, cookies=None) -> bool:
    """Download image with proper headers and cookies"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
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
        return size > 1000  # Valid image should be larger than 1KB
        
    except Exception as e:
        print(f"  ❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def main():
    print("🔄 Re-downloading actual carousel images for C0xFHGOrBN7...")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    print("🤖 Setting up browser...")
    driver = setup_browser()
    
    carousel_urls = [
        "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=1",
        "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=2", 
        "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=3"
    ]
    
    downloaded_images = []
    
    try:
        for i, url in enumerate(carousel_urls, 1):
            print(f"🔍 Loading carousel image {i}: {url}")
            driver.get(url)
        
            # Handle popups only on first load
            if i == 1:
                # Handle cookie popup
                try:
                    wait = WebDriverWait(driver, 10)
                    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
                    accept_btn.click()
                    print("   🍪 Accepted cookies")
                    time.sleep(2)
                except:
                    print("   🍪 No cookie popup or already accepted")
                
                # Handle "See more from" modal
                try:
                    wait = WebDriverWait(driver, 5)
                    close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close' or contains(@aria-label, 'close') or contains(text(), 'Close')]")))
                    close_btn.click()
                    print("   ❌ Closed 'See more from' modal")
                    time.sleep(2)
                except:
                    print("   ❌ No 'See more from' modal found")
            
            # Wait for content to load
            print(f"   ⏳ Waiting for carousel image {i} to load...")
            time.sleep(3)
            
            # Get browser cookies for authenticated requests
            cookies = driver.get_cookies()
            
            # Find the main post image (should be the largest/primary image)
            images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
            print(f"   📊 Found {len(images)} total images for image {i}")
            
            # Look for the main carousel image - prioritize large, main content images
            main_image_src = None
            main_image_alt = ""
            
            # Strategy 1: Look for large images (1440x, 1080x)
            for img in images:
                src = img.get_attribute('src')
                if src and 'profile_pic' not in src:
                    if '1440x' in src or '1080x' in src:
                        main_image_src = src
                        main_image_alt = img.get_attribute('alt') or ""
                        print(f"     Found large carousel image: {src[:100]}...")
                        break
            
            # Strategy 2: Look for medium images if no large ones found
            if not main_image_src:
                for img in images:
                    src = img.get_attribute('src')
                    if src and 'profile_pic' not in src and any(size in src for size in ['640x', '480x']):
                        main_image_src = src
                        main_image_alt = img.get_attribute('alt') or ""
                        print(f"     Found medium carousel image: {src[:100]}...")
                        break
            
            # Strategy 3: Take any Instagram content image (excluding profile pics)
            if not main_image_src:
                for img in images:
                    src = img.get_attribute('src')
                    if (src and 'instagram' in src and 'profile_pic' not in src 
                        and 's150x150' not in src and 'avatar' not in src):
                        main_image_src = src
                        main_image_alt = img.get_attribute('alt') or ""
                        print(f"     Found any content image: {src[:100]}...")
                        break
            
            if main_image_src:
                filename = f"C0xFHGOrBN7_image_{i}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                print(f"📥 Downloading carousel image {i}/3...")
                if download_image(main_image_src, filepath, cookies):
                    downloaded_images.append((main_image_src, main_image_alt))
                
                time.sleep(1)  # Small delay between downloads
            else:
                print(f"   ❌ Could not find main image for carousel position {i}")
        
        downloaded = len(downloaded_images)
        
        # Update extraction info
        info_path = os.path.join(output_dir, "extraction_info.txt")
        with open(info_path, 'w') as f:
            f.write(f"Post: C0xFHGOrBN7\n")
            f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\n")
            f.write(f"Images extracted: {downloaded}\n")
            f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Method: Direct carousel navigation with img_index\n")
            f.write(f"\nImage URLs:\n")
            for i, (src, alt) in enumerate(downloaded_images, 1):
                f.write(f"{i}. {src}\n")
        
        print(f"\\n✅ Successfully downloaded {downloaded} images for C0xFHGOrBN7")
        
    finally:
        print("🔒 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()