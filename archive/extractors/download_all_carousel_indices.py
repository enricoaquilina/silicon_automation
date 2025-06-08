#!/usr/bin/env python3
"""
Download images from all carousel indices to see what's actually available
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
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

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

def extract_main_image_from_page(driver, index):
    """Extract the main carousel image from the current page"""
    time.sleep(5)  # Wait for content to load
    
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    
    # Look for the primary content image (largest, highest quality)
    best_image = None
    best_score = 0
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if "fbcdn.net" in src and "t51.29350-15" in src and "profile_pic" not in src:
            # Score based on likely main content indicators
            score = 0
            
            # High resolution images get higher score
            if "1440x" in src:
                score += 100
            elif "1080x" in src:
                score += 80
            elif "640x" in src:
                score += 60
            
            # Images with December 2023 in alt text are likely main carousel
            if "December 12, 2023" in alt:
                score += 50
            elif "Fanthasia" in alt:
                score += 20
            
            # Prefer earlier images in DOM (usually main content)
            if score > best_score:
                best_image = {"src": src, "alt": alt, "score": score}
                best_score = score
    
    return best_image

def main():
    print("🔍 Checking all carousel indices for C0xFHGOrBN7...")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    carousel_images = []
    
    try:
        # Check indices 1, 2, 3, 4 to see what's available
        for index in range(1, 5):
            url = f"https://www.instagram.com/p/C0xFHGOrBN7/?img_index={index}"
            print(f"\\n🔍 Checking index {index}: {url}")
            
            driver.get(url)
            
            # Handle popups on first load
            if index == 1:
                try:
                    wait = WebDriverWait(driver, 10)
                    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
                    accept_btn.click()
                    print("   🍪 Accepted cookies")
                    time.sleep(2)
                except:
                    print("   🍪 No cookie popup")
                
                # Close any blocking modals
                try:
                    modals = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
                    for modal in modals:
                        if modal.is_displayed():
                            close_btns = modal.find_elements(By.CSS_SELECTOR, "button[aria-label*='Close'], svg[aria-label*='Close']")
                            for btn in close_btns:
                                try:
                                    btn.click()
                                    print("   ❌ Closed modal")
                                    time.sleep(1)
                                    break
                                except:
                                    continue
                except:
                    pass
            
            # Extract the main image from this index
            main_image = extract_main_image_from_page(driver, index)
            
            if main_image:
                # Check if this is a unique image we haven't seen
                image_already_seen = any(
                    existing["src"] == main_image["src"] 
                    for existing in carousel_images
                )
                
                if not image_already_seen:
                    main_image["index"] = index
                    carousel_images.append(main_image)
                    print(f"   ✅ Found new image: {main_image['alt'][:50]}...")
                    print(f"   📊 Score: {main_image['score']}, URL: {main_image['src'][:80]}...")
                else:
                    print(f"   🔄 Same image as previous index")
            else:
                print(f"   ❌ No main image found for index {index}")
        
        print(f"\\n📊 Found {len(carousel_images)} unique carousel images")
        
        # Get browser cookies for downloads
        cookies = driver.get_cookies()
        
        # Download the unique images
        downloaded = 0
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
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
            f.write(f"Method: Carousel index scanning (img_index=1 to 4)\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
                f.write(f"   From index: {img_data['index']}\\n")
        
        print(f"\\n✅ Successfully downloaded {downloaded} unique carousel images")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()