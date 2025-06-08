#!/usr/bin/env python3
"""
Robust Carousel Navigator - Uses direct URL approach with img_index parameter
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


class RobustCarouselNavigator:
    """Robust carousel navigator using URL index approach"""
    
    def __init__(self, driver=None):
        """Initialize with optional existing driver"""
        self.driver = driver
        self.should_close_driver = False
        
        if not self.driver:
            self.driver = self._setup_browser()
            self.should_close_driver = True
    
    def _setup_browser(self):
        """Setup browser with enhanced settings"""
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
    
    def _close_popups_enhanced(self):
        """Enhanced popup closing with comprehensive modal handling"""
        print("🚪 Closing popups...")
        
        # Step 1: Cookie consent
        cookie_patterns = [
            "//button[contains(text(), 'Allow all cookies')]",
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'Accept')]"
        ]
        
        cookie_dismissed = False
        for pattern in cookie_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Accepted cookies")
                        time.sleep(4)
                        cookie_dismissed = True
                        break
                if cookie_dismissed:
                    break
            except:
                continue
        
        # Step 2: After cookies, wait and look for login/signup modal
        if cookie_dismissed:
            time.sleep(3)  # Wait for modal to appear
        
        # Step 3: Handle login/signup modal with multiple strategies
        modal_patterns = [
            # Standard "Not Now" buttons
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Not now')]", 
            "//a[contains(text(), 'Not now')]",
            
            # Modal close buttons
            "//button[@aria-label='Close']",
            "//button[contains(@aria-label, 'Close')]",
            "[aria-label='Close']",
            
            # SVG close buttons (X buttons)
            "//svg[@aria-label='Close']/../..",
            "//div[contains(@role, 'button')]//*[name()='svg'][@aria-label='Close']/../..",
            
            # Generic modal dismissal
            "//div[contains(@role, 'dialog')]//button",
            "[role='dialog'] button",
            
            # Instagram specific patterns
            "//button[text()='Not Now']",
            "//div[text()='Not Now']/..",
            
            # Backup patterns for modal overlay
            "//div[contains(@class, 'modal')]//button",
            "//div[contains(@style, 'position: fixed')]//button[contains(text(), 'Not')]"
        ]
        
        for pattern in modal_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Try both click methods
                            try:
                                element.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", element)
                            
                            print(f"   ✅ Dismissed modal using pattern: {pattern[:50]}")
                            time.sleep(3)
                            return True
                    except:
                        continue
            except:
                continue
        
        # Step 4: Try escape key to close any remaining modals
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            print(f"   ⌨️ Sent ESC key to close modals")
            time.sleep(2)
        except:
            pass
        
        # Step 5: Try clicking outside modal area (background)
        try:
            # Click on upper left corner to dismiss modal
            ActionChains(self.driver).move_by_offset(50, 50).click().perform()
            print(f"   🖱️ Clicked outside modal area")
            time.sleep(2)
        except:
            pass
        
        return True
    
    def _get_image_hash(self, image_bytes):
        """Get hash of image content"""
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
    
    def _find_carousel_image_precisely(self):
        """Find the main carousel image with precise targeting"""
        time.sleep(3)  # Wait for images to load
        
        # Try multiple strategies to find the main carousel image
        strategies = [
            "article img[src*='t51.29350-15']",  # Main article images
            "main img[src*='t51.29350-15']",     # Main container images
            "img[src*='t51.29350-15']"           # General high-quality images
        ]
        
        for strategy in strategies:
            try:
                images = self.driver.find_elements(By.CSS_SELECTOR, strategy)
                for img in images:
                    try:
                        src = img.get_attribute('src')
                        alt = img.get_attribute('alt') or ''
                        location = img.location
                        
                        # Filter for main carousel images only
                        if (src and 
                            't51.29350-15' in src and 
                            't51.2885-19' not in src and  # Not profile images
                            location['y'] < 600 and       # Upper part of page
                            location['x'] > 100 and       # Not in sidebar
                            img.is_displayed()):
                            
                            print(f"      📸 Found image: {alt[:50]}")
                            return {
                                'src': src,
                                'alt': alt,
                                'location': location
                            }
                    except:
                        continue
            except:
                continue
        
        return None
    
    def _test_url_index_approach(self, shortcode, max_index=15):
        """Test direct URL approach with img_index parameter"""
        print(f"\n🔗 Testing URL index approach for {shortcode}...")
        
        found_images = []
        
        for index in range(1, max_index + 1):
            test_url = f"https://www.instagram.com/p/{shortcode}/?img_index={index}"
            print(f"   Testing index {index}")
            
            try:
                self.driver.get(test_url)
                time.sleep(6)  # Wait for page load
                
                # Close popups on EVERY index load since they pop up repeatedly
                self._close_popups_enhanced()
                time.sleep(2)
                
                # Look for image at this index
                image = self._find_carousel_image_precisely()
                if image:
                    # Check if this is a new unique image by comparing URLs
                    existing_srcs = [img['src'] for img in found_images]
                    if image['src'] not in existing_srcs:
                        found_images.append(image)
                        print(f"      ✅ Found new image {len(found_images)}: {image['alt'][:40]}")
                        print(f"         URL: {image['src'][:80]}...")
                    else:
                        print(f"      🔄 Same image as before (end of carousel)")
                        print(f"         URL: {image['src'][:80]}...")
                        break
                else:
                    print(f"      ❌ No image found at index {index}")
                    break
                    
            except Exception as e:
                print(f"      ❌ Error at index {index}: {str(e)[:50]}")
                break
        
        return found_images
    
    def extract_robust_carousel(self, shortcode, output_directory):
        """Extract carousel using URL index approach"""
        print(f"🎯 ROBUST CAROUSEL EXTRACTION for {shortcode}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Use URL index approach to find all carousel images
        carousel_images = self._test_url_index_approach(shortcode, max_index=20)
        
        print(f"\n📊 Extraction complete:")
        print(f"   Total carousel images: {len(carousel_images)}")
        
        # Download all images
        print(f"\n📥 Downloading carousel images...")
        os.makedirs(output_directory, exist_ok=True)
        
        unique_images = []
        existing_hashes = set()
        
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"robust_{shortcode}_carousel_{i}.jpg"
            filepath = os.path.join(output_directory, filename)
            
            success, img_hash, size = self._download_image(img_data['src'], filepath, existing_hashes)
            if success:
                unique_images.append({
                    'index': i,
                    'url': img_data['src'],
                    'filename': filename,
                    'size': size,
                    'hash': img_hash,
                    'alt': img_data['alt']
                })
                print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
        
        duration = time.time() - start_time
        
        # Create results
        results = {
            'shortcode': shortcode,
            'total_extracted': len(unique_images),
            'images': unique_images,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': len(unique_images) > 0,
            'extraction_method': 'robust_url_index',
            'duration_seconds': round(duration, 2)
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, f"robust_results_{shortcode}.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 ROBUST EXTRACTION COMPLETE")
        print(f"📊 Carousel images: {len(unique_images)}")
        print(f"⏱️ Duration: {duration:.1f}s")
        
        if unique_images:
            print(f"📁 Robust carousel images:")
            for img in unique_images:
                print(f"   • {img['filename']} - {img['alt'][:50]}")
        
        print("=" * 60)
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Test both carousels
    test_cases = [
        ("C0xFHGOrBN7", "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"),
        ("C0wmEEKItfR", "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0wmEEKItfR")
    ]
    
    for shortcode, output_dir in test_cases:
        print(f"\n{'='*80}")
        print(f"TESTING ROBUST EXTRACTION: {shortcode}")
        print(f"{'='*80}")
        
        extractor = RobustCarouselNavigator()
        try:
            results = extractor.extract_robust_carousel(shortcode, output_dir)
            
            print(f"\n📈 ASSESSMENT for {shortcode}:")
            print(f"   Images extracted: {results['total_extracted']}")
            print(f"   Success: {'✅ EXCELLENT' if results['total_extracted'] >= 3 else '⚠️ PARTIAL' if results['total_extracted'] > 1 else '❌ FAILED'}")
            
        finally:
            extractor.close()
        
        time.sleep(3)  # Brief pause between tests