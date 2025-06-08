#!/usr/bin/env python3
"""
Extract truly unique carousel images by comparing image IDs and using comprehensive search
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

def extract_image_id(url):
    """Extract the unique image ID from Instagram URL"""
    match = re.search(r'/([0-9]+)_([0-9]+)_[0-9]+_n\.jpg', url)
    if match:
        return match.group(1)  # First ID is usually the unique identifier
    return None

def get_all_images_from_page(driver, page_index):
    """Get all potential carousel images from current page"""
    time.sleep(5)
    
    images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
    found_images = []
    
    for img in images:
        src = img.get_attribute("src") or ""
        alt = img.get_attribute("alt") or ""
        
        if "fbcdn.net" in src and "t51.29350-15" in src and "profile_pic" not in src:
            image_id = extract_image_id(src)
            if image_id:
                found_images.append({
                    "src": src,
                    "alt": alt,
                    "image_id": image_id,
                    "page_index": page_index,
                    "priority": 0  # Will be set based on scoring
                })
    
    # Score images based on likely relevance to main carousel
    for img in found_images:
        score = 0
        
        # High resolution gets priority
        if "1440x" in img["src"]:
            score += 100
        elif "1080x" in img["src"]:
            score += 80
        elif "640x" in img["src"]:
            score += 60
        
        # December 2023 images are likely main carousel
        if "December 12, 2023" in img["alt"]:
            score += 50
        elif "Fanthasia" in img["alt"] and "2023" in img["alt"]:
            score += 30
        elif "Fanthasia" in img["alt"]:
            score += 10
        
        img["priority"] = score
    
    # Sort by priority (highest first)
    found_images.sort(key=lambda x: x["priority"], reverse=True)
    
    return found_images

def main():
    print("🔍 Extracting unique carousel images for C0xFHGOrBN7...")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    unique_images = {}  # Dictionary keyed by image_id to store unique images
    
    try:
        # Check multiple carousel indices and also the main page
        urls_to_check = [
            "https://www.instagram.com/p/C0xFHGOrBN7/",
            "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=1",
            "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=2",
            "https://www.instagram.com/p/C0xFHGOrBN7/?img_index=3",
        ]
        
        for i, url in enumerate(urls_to_check):
            print(f"\\n🔍 Scanning {url}")
            driver.get(url)
            
            # Handle popups on first load
            if i == 0:
                try:
                    wait = WebDriverWait(driver, 10)
                    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
                    accept_btn.click()
                    print("   🍪 Accepted cookies")
                    time.sleep(2)
                except:
                    print("   🍪 No cookie popup")
                
                # Close modals
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
            
            # Get images from this page
            page_images = get_all_images_from_page(driver, i)
            
            # Add unique images to our collection
            for img in page_images:
                image_id = img["image_id"]
                
                # Only add if we haven't seen this image ID before, or if this version has higher priority
                if image_id not in unique_images or img["priority"] > unique_images[image_id]["priority"]:
                    unique_images[image_id] = img
                    print(f"   ✅ Found image ID {image_id}: {img['alt'][:50]}... (priority: {img['priority']})")
                else:
                    print(f"   🔄 Already have image ID {image_id}")
        
        # Sort unique images by priority and take the top ones
        sorted_images = sorted(unique_images.values(), key=lambda x: x["priority"], reverse=True)
        
        print(f"\\n📊 Found {len(sorted_images)} unique images")
        for i, img in enumerate(sorted_images, 1):
            print(f"   {i}. ID: {img['image_id']}, Priority: {img['priority']}, Alt: {img['alt'][:50]}...")
        
        # Download the top 3 unique images
        carousel_images = sorted_images[:3]
        
        # Get browser cookies for downloads
        cookies = driver.get_cookies()
        
        downloaded = 0
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"C0xFHGOrBN7_image_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"\\n📥 Downloading image {i}/{len(carousel_images)}...")
            print(f"   ID: {img_data['image_id']}, Alt: {img_data['alt']}")
            
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
            f.write(f"Method: Multi-page scan with unique image ID detection\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
                f.write(f"   Priority: {img_data['priority']}\\n")
        
        print(f"\\n✅ Successfully downloaded {downloaded} unique carousel images")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()