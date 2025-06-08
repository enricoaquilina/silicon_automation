#!/usr/bin/env python3
"""
Carousel Extractor - TDD Implementation
This will be built iteratively to pass all tests
"""

import os
import time
import hashlib
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import re


class CarouselExtractor:
    """Test-driven carousel image extractor"""
    
    def __init__(self, driver=None):
        """Initialize with optional existing driver"""
        self.driver = driver
        self.should_close_driver = False
        
        if not self.driver:
            self.driver = self._setup_browser()
            self.should_close_driver = True
    
    def _setup_browser(self):
        """Setup browser with optimal settings"""
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
    
    def _close_popups(self):
        """Close Instagram popups including cookie consent and login prompts"""
        # First round: Cookie consent
        cookie_patterns = [
            "//button[contains(text(), 'Allow all cookies')]",
            "//button[contains(text(), 'Accept all')]", 
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Allow essential and optional cookies')]"
        ]
        
        for pattern in cookie_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Accepted cookies")
                        time.sleep(3)
                        break
            except:
                continue
        
        # Second round: Login/signup prompts
        login_patterns = [
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Not now')]",
            "//a[contains(text(), 'Not now')]",
            "//span[contains(text(), 'Not now')]/..",
            "//button[@aria-label='Close']",
            "//button[contains(@class, 'close')]",
            "//div[@role='dialog']//button[2]",  # Usually the second button is "Not now"
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Not')]"
        ]
        
        for pattern in login_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Dismissed login prompt")
                        time.sleep(2)
                        break
            except:
                continue
    
    def _get_image_hash(self, image_bytes):
        """Get hash of image content for duplicate detection"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def _download_image(self, url, filepath, existing_hashes):
        """Download image if unique"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            image_hash = self._get_image_hash(response.content)
            if image_hash in existing_hashes:
                return False, image_hash, 0
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            size = len(response.content)
            existing_hashes.add(image_hash)
            return True, image_hash, size
            
        except Exception as e:
            print(f"Download failed: {e}")
            return False, None, 0
    
    def _find_carousel_images(self):
        """Find all images in current carousel view"""
        # Look for high-quality Instagram images (now using fbcdn)
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        carousel_images = []
        for img in images:
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                # Filter for high-quality post images only
                if (src and 
                    't51.29350-15' in src and  # High resolution post images
                    not any(exclude in src for exclude in ['t51.2885-19']) and  # Profile images
                    img.is_displayed()):
                    
                    carousel_images.append({
                        'src': src,
                        'alt': alt,
                        'visible': img.is_displayed()
                    })
            except:
                continue
        
        return carousel_images
    
    def _navigate_next(self):
        """Navigate to next image in carousel"""
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label='Next']",
            "[role='button'][aria-label*='Next']",
            "div[role='button'][aria-label*='Next']"
        ]
        
        for selector in next_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        # Try multiple click methods
                        try:
                            ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                        except:
                            try:
                                btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", btn)
                        
                        time.sleep(3)  # Wait for navigation
                        return True
            except:
                continue
        
        return False
    
    def extract_all_images(self, shortcode, output_directory):
        """Extract all images from carousel - main method"""
        print(f"🚀 Starting extraction for {shortcode}")
        
        # Navigate to post
        url = f"https://www.instagram.com/p/{shortcode}/"
        self.driver.get(url)
        time.sleep(8)
        
        # Close popups
        self._close_popups()
        time.sleep(3)
        
        # Collect all unique images
        all_image_urls = set()
        navigation_attempts = 0
        max_attempts = 15
        
        # Get initial images
        initial_images = self._find_carousel_images()
        for img in initial_images:
            all_image_urls.add(img['src'])
        
        print(f"📊 Found {len(initial_images)} initial images")
        
        # Navigate through carousel
        while navigation_attempts < max_attempts:
            before_count = len(all_image_urls)
            
            if self._navigate_next():
                # Check for new images
                current_images = self._find_carousel_images()
                new_images = 0
                
                for img in current_images:
                    if img['src'] not in all_image_urls:
                        all_image_urls.add(img['src'])
                        new_images += 1
                
                if new_images == 0:
                    print(f"🛑 No new images found, stopping navigation")
                    break
                else:
                    print(f"➡️ Navigation {navigation_attempts + 1}: +{new_images} images")
            else:
                print(f"❌ Navigation failed at attempt {navigation_attempts + 1}")
                break
            
            navigation_attempts += 1
        
        print(f"📋 Total unique image URLs collected: {len(all_image_urls)}")
        
        # Download all unique images
        os.makedirs(output_directory, exist_ok=True)
        unique_images = []
        existing_hashes = set()
        
        for i, img_url in enumerate(all_image_urls, 1):
            filename = f"test_{shortcode}_image_{i}.jpg"
            filepath = os.path.join(output_directory, filename)
            
            success, img_hash, size = self._download_image(img_url, filepath, existing_hashes)
            if success:
                unique_images.append({
                    'index': i,
                    'url': img_url,
                    'filename': filename,
                    'size': size,
                    'hash': img_hash
                })
                print(f"✅ Downloaded: {filename} ({size} bytes)")
        
        # Create results
        results = {
            'shortcode': shortcode,
            'total_extracted': len(unique_images),
            'images': unique_images,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': len(unique_images) > 0,
            'navigation_attempts': navigation_attempts
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, "test_extraction_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"🎯 Extraction complete: {len(unique_images)} unique images")
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Quick test
    extractor = CarouselExtractor()
    try:
        results = extractor.extract_all_images(
            "C0xFHGOrBN7", 
            "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
        )
        print(f"Results: {results['total_extracted']} images extracted")
    finally:
        extractor.close()