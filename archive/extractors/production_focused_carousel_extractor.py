#!/usr/bin/env python3
"""
Production Focused Carousel Extractor
Improved version that extracts ONLY actual carousel images, not suggested content
"""

import os
import time
import hashlib
import requests
import json
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


class ProductionFocusedCarouselExtractor:
    """Production carousel extractor that filters out suggested content"""
    
    def __init__(self, driver=None):
        """Initialize with optional existing driver"""
        self.driver = driver
        self.should_close_driver = False
        
        if not self.driver:
            self.driver = self._setup_browser()
            self.should_close_driver = True
    
    def _setup_browser(self):
        """Setup browser with maximum stealth"""
        options = Options()
        
        # Enhanced anti-detection
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--window-size=1920,1080")
        
        # Disable password manager prompts
        prefs = {
            "profile.default_content_setting_values": {"notifications": 2},
            "profile.password_manager_enabled": False,
            "credentials_enable_service": False,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _close_popups_comprehensive(self):
        """Comprehensive popup closing with multiple rounds"""
        print("🚪 Closing all popups and modals...")
        
        # Round 1: Cookie consent
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
                        return  # Exit after first successful click
            except:
                continue
        
        # Round 2: Login/signup prompts
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
                        print(f"   ✅ Dismissed login/signup prompt")
                        time.sleep(2)
                        return  # Exit after first successful click
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
    
    def _get_carousel_images_filtered(self):
        """Get carousel images with comprehensive filtering to exclude suggested content"""
        # Find all high-quality images
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        potential_images = []
        for img in images:
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                # Filter for high-quality post images
                if (src and 
                    't51.29350-15' in src and  # High resolution post images
                    't51.2885-19' not in src and  # Exclude profile images
                    img.is_displayed()):
                    
                    location = img.location
                    
                    potential_images.append({
                        'src': src,
                        'alt': alt,
                        'location': location,
                        'y_position': location['y'],
                        'x_position': location['x'],
                        'element': img
                    })
            except Exception as e:
                continue
        
        if not potential_images:
            print("❌ No potential carousel images found")
            return []
        
        # Sort by Y position to understand page layout
        potential_images.sort(key=lambda x: x['y_position'])
        
        print(f"📊 Found {len(potential_images)} potential images")
        
        # Group images by Y position proximity (within 200px)
        groups = []
        current_group = [potential_images[0]]
        
        for img in potential_images[1:]:
            if abs(img['y_position'] - current_group[-1]['y_position']) < 200:
                current_group.append(img)
            else:
                groups.append(current_group)
                current_group = [img]
        
        if current_group:
            groups.append(current_group)
        
        print(f"🎯 Grouped into {len(groups)} position clusters:")
        for i, group in enumerate(groups):
            y_min = min(img['y_position'] for img in group)
            y_max = max(img['y_position'] for img in group)
            print(f"   Group {i+1}: {len(group)} images at Y {y_min}-{y_max}")
        
        # The first group (topmost) contains the carousel images
        if not groups:
            return []
        
        carousel_candidates = groups[0]
        print(f"🎯 Selected top group as carousel: {len(carousel_candidates)} images")
        
        # Additional filtering for main post content
        filtered_carousel = []
        for img_data in carousel_candidates:
            try:
                # Position-based filtering: carousel images should be near top of page
                if img_data['y_position'] < 600:  # Adjust threshold as needed
                    
                    # Content-based filtering: check alt text for carousel indicators
                    alt = img_data['alt']
                    
                    # Exclude images with clear "suggested" or "more posts" indicators
                    exclude_keywords = ['more posts', 'suggested', 'related', 'explore', 'recent']
                    is_excluded = any(keyword in alt.lower() for keyword in exclude_keywords)
                    
                    if not is_excluded:
                        filtered_carousel.append({
                            'src': img_data['src'],
                            'alt': alt,
                            'location': img_data['location']
                        })
                        
            except Exception as e:
                # If filtering fails, include conservatively
                filtered_carousel.append({
                    'src': img_data['src'],
                    'alt': img_data['alt'],
                    'location': img_data['location']
                })
        
        print(f"✅ Final filtered carousel: {len(filtered_carousel)} images")
        return filtered_carousel
    
    def _navigate_carousel(self):
        """Enhanced carousel navigation"""
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
                        try:
                            # Method 1: ActionChains with hover
                            ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                            return True
                        except:
                            try:
                                # Method 2: Direct click
                                btn.click()
                                return True
                            except:
                                try:
                                    # Method 3: JavaScript click
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    return True
                                except:
                                    continue
            except:
                continue
        
        return False
    
    def extract_carousel_focused(self, shortcode, output_directory):
        """Main extraction method - focused on carousel only"""
        print(f"🎯 PRODUCTION FOCUSED EXTRACTION for {shortcode}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Navigate to post
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔗 Loading: {url}")
        self.driver.get(url)
        time.sleep(8)
        
        # Close all popups
        self._close_popups_comprehensive()
        time.sleep(3)
        
        # Collect unique carousel images through navigation
        all_carousel_urls = set()
        navigation_attempts = 0
        max_navigation_attempts = 15
        
        # Phase 1: Get initial carousel images
        print(f"📸 Phase 1: Initial carousel detection...")
        initial_images = self._get_carousel_images_filtered()
        for img in initial_images:
            all_carousel_urls.add(img['src'])
        initial_count = len(initial_images)
        print(f"   Found {initial_count} initial carousel images")
        
        # Phase 2: Navigate through carousel
        print(f"🔄 Phase 2: Carousel navigation...")
        while navigation_attempts < max_navigation_attempts:
            before_count = len(all_carousel_urls)
            
            # Try to navigate to next image
            if self._navigate_carousel():
                print(f"   ➡️ Navigation attempt {navigation_attempts + 1} succeeded")
                time.sleep(3)
                
                # Check for new carousel images
                current_images = self._get_carousel_images_filtered()
                new_images = 0
                
                for img in current_images:
                    if img['src'] not in all_carousel_urls:
                        all_carousel_urls.add(img['src'])
                        new_images += 1
                
                if new_images > 0:
                    print(f"   🆕 Found {new_images} new carousel images")
                else:
                    print(f"   🛑 No new images found, stopping navigation")
                    break
                    
            else:
                print(f"   ❌ Navigation attempt {navigation_attempts + 1} failed")
                break
            
            navigation_attempts += 1
        
        total_unique_urls = len(all_carousel_urls)
        print(f"📋 Total unique carousel URLs: {total_unique_urls}")
        
        # Phase 3: Download images
        print(f"📥 Phase 3: Downloading carousel images...")
        os.makedirs(output_directory, exist_ok=True)
        
        unique_images = []
        existing_hashes = set()
        
        for i, img_url in enumerate(all_carousel_urls, 1):
            filename = f"carousel_{shortcode}_image_{i}.jpg"
            filepath = os.path.join(output_directory, filename)
            
            print(f"   Downloading {i}/{total_unique_urls}: {filename}")
            success, img_hash, size = self._download_image(img_url, filepath, existing_hashes)
            
            if success:
                unique_images.append({
                    'index': i,
                    'url': img_url,
                    'filename': filename,
                    'size': size,
                    'hash': img_hash
                })
                print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
            else:
                print(f"   ❌ Failed to download: {filename}")
        
        duration = time.time() - start_time
        
        # Create comprehensive results
        results = {
            'shortcode': shortcode,
            'total_extracted': len(unique_images),
            'images': unique_images,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': len(unique_images) > 0,
            'navigation_attempts': navigation_attempts,
            'initial_images_found': initial_count,
            'extraction_method': 'production_focused_carousel',
            'duration_seconds': round(duration, 2),
            'performance': {
                'images_per_second': round(len(unique_images) / duration, 2) if duration > 0 else 0,
                'avg_download_time': round(duration / len(unique_images), 2) if unique_images else 0
            }
        }
        
        # Save detailed metadata
        results_path = os.path.join(output_directory, f"production_focused_results_{shortcode}.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n🎉 EXTRACTION COMPLETE")
        print(f"📊 Results: {len(unique_images)} carousel images")
        print(f"⏱️ Duration: {duration:.1f}s")
        print(f"🚀 Performance: {results['performance']['images_per_second']:.1f} images/sec")
        
        if unique_images:
            print(f"📁 Downloaded files:")
            for img in unique_images:
                print(f"   • {img['filename']} ({img['size']:,} bytes)")
        
        print("=" * 60)
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Test the production focused extractor
    extractor = ProductionFocusedCarouselExtractor()
    try:
        results = extractor.extract_carousel_focused(
            "C0wmEEKItfR", 
            "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0wmEEKItfR"
        )
        
        success_rate = (results['total_extracted'] / results['initial_images_found'] * 100) if results['initial_images_found'] > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
    finally:
        extractor.close()