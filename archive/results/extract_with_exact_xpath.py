#!/usr/bin/env python3
"""
Extract carousel images using the exact XPath for the Next button
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
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser with human-like behavior"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
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
            
            # Check if image is actually visible/displayed
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

def main():
    print("🔍 Extracting carousel images using exact XPath for C0xFHGOrBN7...")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    carousel_images = []
    seen_image_ids = set()
    
    # Exact XPath for the Next button as provided by user
    next_button_xpath = "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[1]/div/div/div/div/div[1]/div/div[1]/div[2]/div/button[2]"
    
    try:
        # Load the main post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        
        # Handle initial popups
        try:
            wait = WebDriverWait(driver, 10)
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
            accept_btn.click()
            print("   🍪 Accepted cookies")
            time.sleep(3)
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
                            time.sleep(2)
                            break
                        except:
                            continue
        except:
            pass
        
        # Wait for content to load properly
        print("   ⏳ Waiting for content to load...")
        time.sleep(8)
        
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
        
        # Navigate through carousel using the exact XPath
        for i in range(2, 5):  # Try to get images 2, 3, 4
            print(f"\\n📸 Looking for image {i}...")
            
            try:
                # Find the Next button using exact XPath
                print(f"   🔍 Looking for Next button with XPath...")
                next_btn = driver.find_element(By.XPATH, next_button_xpath)
                
                if next_btn.is_displayed() and next_btn.is_enabled():
                    print(f"   ✅ Found Next button with exact XPath")
                    
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(1)
                    
                    # Click the button
                    actions = ActionChains(driver)
                    actions.move_to_element(next_btn).click().perform()
                    print(f"   🖱️  Clicked Next button")
                    
                    # Wait for new image to load
                    time.sleep(4)
                    
                    # Extract image from new view
                    current_image = get_main_image_from_current_view(driver)
                    if current_image and current_image["image_id"]:
                        if current_image["image_id"] not in seen_image_ids:
                            carousel_images.append(current_image)
                            seen_image_ids.add(current_image["image_id"])
                            print(f"   ✅ Found new image: {current_image['alt'][:50]}... (ID: {current_image['image_id']})")
                        else:
                            print(f"   🔄 Same image as before (ID: {current_image['image_id']}) - reached end")
                            break
                    else:
                        print("   ❌ Could not extract image from current view")
                        break
                else:
                    print(f"   ❌ Next button found but not clickable")
                    break
                    
            except Exception as e:
                print(f"   ❌ Could not find Next button with exact XPath: {e}")
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
            f.write(f"Method: Carousel navigation with exact XPath Next button\\n")
            f.write(f"Next button XPath: {next_button_xpath}\\n")
            f.write(f"\\nImage URLs:\\n")
            for i, img_data in enumerate(carousel_images[:downloaded], 1):
                f.write(f"{i}. {img_data['src']}\\n")
                f.write(f"   Image ID: {img_data['image_id']}\\n")
                f.write(f"   Alt: {img_data['alt']}\\n")
                f.write(f"   Score: {img_data['score']}\\n")
        
        print(f"\\n✅ Successfully extracted and downloaded {downloaded} carousel images using exact XPath")
        
        # Keep browser open for a moment to verify
        print("\\n👀 Keeping browser open for 10 seconds for verification...")
        time.sleep(10)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()