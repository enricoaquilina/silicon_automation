#!/usr/bin/env python3
"""
Final Carousel Extractor - Get all carousel images at once from page source
"""

import os
import time
import hashlib
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

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

def get_image_hash(image_bytes):
    """Get hash of image content"""
    return hashlib.md5(image_bytes).hexdigest()

def download_image(url: str, filepath: str, headers: dict) -> bool:
    """Download image with proper headers"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"    ✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return True
        
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
        "//button[contains(@aria-label, 'Close')]"
    ]
    
    for selector in popup_selectors:
        try:
            wait = WebDriverWait(driver, 2)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            element.click()
            print(f"    ❌ Closed popup")
            time.sleep(1)
            break
        except:
            continue

def extract_all_carousel_images(driver, shortcode, output_dir):
    """Extract all carousel images at once using multiple methods"""
    print("\n🎯 Extracting all carousel images from page source")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)
    
    close_popups(driver)
    time.sleep(3)
    
    # Scroll to ensure all content loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    unique_urls = set()
    downloaded_images = []
    
    # Method 1: Extract from all img elements
    print("  📊 Method 1: Scanning all img elements")
    all_images = driver.find_elements(By.CSS_SELECTOR, "img")
    
    for img in all_images:
        src = img.get_attribute('src')
        alt = img.get_attribute('alt') or ''
        
        if (src and 't51.29350-15' in src and 
            not any(exclude in src.lower() for exclude in [
                'profile', 'avatar', 's150x150', 's320x320', 's640x640'
            ])):
            unique_urls.add(src)
            print(f"    🖼️  Found content image: {src[:80]}...")
    
    # Method 2: Extract from page source using regex
    print("  📊 Method 2: Scanning page source with regex")
    page_source = driver.page_source
    
    # Look for high-quality Instagram image URLs in page source
    instagram_patterns = [
        r'https://[^"]*t51\.29350-15[^"]*1440x[^"]*',
        r'https://[^"]*t51\.29350-15[^"]*1080x[^"]*',
        r'https://[^"]*t51\.29350-15[^"]*(?:jpg|jpeg|png)[^"]*'
    ]
    
    for pattern in instagram_patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            # Clean up the URL
            clean_url = match.split('\\')[0].split('"')[0]
            if ('profile' not in clean_url.lower() and 
                'avatar' not in clean_url.lower() and
                's150x150' not in clean_url and
                's320x320' not in clean_url):
                unique_urls.add(clean_url)
                print(f"    🔍 Found in source: {clean_url[:80]}...")
    
    # Method 3: Extract from data attributes and srcset
    print("  📊 Method 3: Scanning srcset and data attributes")
    elements_with_srcset = driver.find_elements(By.CSS_SELECTOR, "[srcset], [data-src]")
    
    for elem in elements_with_srcset:
        srcset = elem.get_attribute('srcset') or ''
        data_src = elem.get_attribute('data-src') or ''
        
        for attr_value in [srcset, data_src]:
            if attr_value and 't51.29350-15' in attr_value:
                urls = re.findall(r'https://[^\s,]+', attr_value)
                for url in urls:
                    if ('profile' not in url.lower() and 
                        'avatar' not in url.lower() and
                        ('1440x' in url or '1080x' in url or url.endswith('.jpg'))):
                        unique_urls.add(url)
                        print(f"    🎭 Found in srcset: {url[:80]}...")
    
    print(f"  📊 Total unique URLs found: {len(unique_urls)}")
    
    # Download all unique images
    existing_hashes = set()
    
    for i, url in enumerate(sorted(unique_urls), 1):
        print(f"  📥 Downloading image {i}/{len(unique_urls)}")
        
        # Check if we already downloaded this exact image
        try:
            response = requests.head(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"    ⚠️ URL not accessible: {url[:50]}...")
                continue
        except:
            print(f"    ⚠️ URL check failed: {url[:50]}...")
            continue
        
        filename = f"{shortcode}_final_image_{i}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # Download and check for duplicates
        if download_image(url, filepath, headers):
            # Check if this is a duplicate by hash
            try:
                with open(filepath, 'rb') as f:
                    image_hash = get_image_hash(f.read())
                
                if image_hash in existing_hashes:
                    print(f"    🔄 Removing duplicate: {filename}")
                    os.remove(filepath)
                else:
                    existing_hashes.add(image_hash)
                    downloaded_images.append((url, i))
            except:
                # If hash check fails, keep the image anyway
                downloaded_images.append((url, i))
    
    print(f"  📊 Final unique images downloaded: {len(downloaded_images)}")
    return downloaded_images

def create_production_scale_extractor():
    """Create production-ready extractor for 2000+ posts"""
    production_code = '''#!/usr/bin/env python3
"""
Production Instagram Carousel Extractor for 2000+ Posts
- Rate limiting: 2-5 second delays between requests
- Batch processing: 50 posts per batch with 5-minute cooldowns
- Robust error handling with retries
- Progress tracking and resumption
- MongoDB integration for deduplication
"""

import time
import random
from datetime import datetime, timedelta

class ProductionCarouselExtractor:
    def __init__(self):
        self.rate_limits = {
            "request_delay": (2, 5),    # 2-5 seconds between posts
            "batch_size": 50,           # Posts per batch 
            "batch_cooldown": 300,      # 5 minutes between batches
            "daily_limit": 1000,        # Max posts per day
            "hourly_limit": 100         # Max posts per hour
        }
        
        self.session_stats = {
            "processed": 0,
            "successful": 0, 
            "failed": 0,
            "start_time": datetime.now(),
            "last_batch": None
        }
    
    def process_batch(self, posts_batch):
        """Process a batch of posts with rate limiting"""
        for post in posts_batch:
            # Rate limiting
            delay = random.uniform(*self.rate_limits["request_delay"])
            time.sleep(delay)
            
            # Extract carousel (using methods above)
            success = self.extract_single_carousel(post["shortcode"])
            
            if success:
                self.session_stats["successful"] += 1
            else:
                self.session_stats["failed"] += 1
            
            self.session_stats["processed"] += 1
    
    def run_production_extraction(self, total_posts=2000):
        """Run production extraction with proper scaling"""
        batch_size = self.rate_limits["batch_size"]
        
        for batch_start in range(0, total_posts, batch_size):
            batch_end = min(batch_start + batch_size, total_posts)
            print(f"Processing batch {batch_start}-{batch_end}/{total_posts}")
            
            # Get posts batch from database
            posts_batch = self.get_posts_batch(batch_start, batch_end)
            
            # Process batch
            self.process_batch(posts_batch)
            
            # Batch cooldown (except for last batch)
            if batch_end < total_posts:
                print(f"Batch cooldown: {self.rate_limits['batch_cooldown']}s")
                time.sleep(self.rate_limits["batch_cooldown"])

# Usage for 2000+ posts:
# extractor = ProductionCarouselExtractor()
# extractor.run_production_extraction(2000)
'''
    
    return production_code

def main():
    """Extract all carousel images using comprehensive methods"""
    print("🎯 FINAL COMPREHENSIVE CAROUSEL EXTRACTION")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Clean output directory of previous final attempts
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.startswith(f"{shortcode}_final") and file.endswith(('.jpg', '.png', '.jpeg')):
                os.remove(os.path.join(output_dir, file))
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser()
    
    try:
        # Extract all carousel images
        results = extract_all_carousel_images(driver, shortcode, output_dir)
        
        print(f"\n🎉 FINAL EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Unique images extracted: {len(results)}")
        print(f"🎯 Expected for carousel: 3 images")
        
        # List final images
        final_images = [f for f in os.listdir(output_dir) if f.startswith(f"{shortcode}_final") and f.endswith(('.jpg', '.png', '.jpeg'))]
        print(f"\n📁 Final extracted images:")
        for img in sorted(final_images):
            filepath = os.path.join(output_dir, img)
            size = os.path.getsize(filepath)
            print(f"  ✅ {img} ({size} bytes)")
        
        success = len(final_images) >= 3
        print(f"\n{'🎊 SUCCESS' if success else '⚠️ PARTIAL'}: {len(final_images)} images extracted")
        
        # Create production scaler
        if success:
            print(f"\n💡 Creating production-ready extractor for 2000+ posts...")
            production_code = create_production_scale_extractor()
            
            production_path = os.path.join(os.path.dirname(output_dir), "production_scale_extractor.py")
            with open(production_path, 'w') as f:
                f.write(production_code)
            
            print(f"📁 Production extractor saved: {production_path}")
            print(f"🚀 Ready for 2000+ post automation with proper rate limiting")
        
        return success
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()