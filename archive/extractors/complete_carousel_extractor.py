#!/usr/bin/env python3
"""
Complete Carousel Extractor - Extracts ALL carousel images using URL pattern analysis
"""

import os
import time
import hashlib
import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


class CompleteCarouselExtractor:
    """Complete carousel extractor that finds ALL carousel images"""
    
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
        """Close Instagram popups"""
        cookie_patterns = [
            "//button[contains(text(), 'Allow all cookies')]",
            "//button[contains(text(), 'Accept all')]", 
            "//button[contains(text(), 'Accept')]"
        ]
        
        for pattern in cookie_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Accepted cookies")
                        time.sleep(3)
                        return
            except:
                continue
        
        login_patterns = [
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Not now')]",
            "//a[contains(text(), 'Not now')]"
        ]
        
        for pattern in login_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Dismissed login prompt")
                        time.sleep(2)
                        return
            except:
                continue
    
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
    
    def _analyze_image_url(self, url):
        """Analyze image URL to determine if it's carousel content"""
        try:
            # Look for efg parameter which contains the image type
            efg_match = re.search(r'efg=([^&]+)', url)
            if efg_match:
                import base64
                try:
                    # Decode the efg parameter
                    efg_decoded = base64.b64decode(efg_match.group(1) + '==').decode('utf-8')
                    
                    # Check if it's carousel content
                    is_carousel = 'CAROUSEL_ITEM' in efg_decoded
                    is_feed = 'FEED' in efg_decoded
                    
                    return {
                        'is_carousel': is_carousel,
                        'is_feed': is_feed,
                        'efg_content': efg_decoded
                    }
                except:
                    pass
            
            # Fallback: analyze cache key patterns
            cache_key_match = re.search(r'ig_cache_key=([^&%]+)', url)
            if cache_key_match:
                cache_key = cache_key_match.group(1)
                # Carousel images often have specific cache key patterns
                return {
                    'is_carousel': True,  # Assume carousel if we can't decode efg
                    'is_feed': False,
                    'cache_key': cache_key
                }
            
        except Exception as e:
            print(f"URL analysis error: {e}")
        
        return {'is_carousel': False, 'is_feed': False}
    
    def _get_all_images_with_analysis(self):
        """Get all images with URL analysis"""
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        analyzed_images = []
        for img in images:
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                if (src and 
                    't51.29350-15' in src and 
                    't51.2885-19' not in src and 
                    img.is_displayed()):
                    
                    location = img.location
                    analysis = self._analyze_image_url(src)
                    
                    analyzed_images.append({
                        'src': src,
                        'alt': alt,
                        'location': location,
                        'analysis': analysis,
                        'y_position': location['y']
                    })
            except:
                continue
        
        return analyzed_images
    
    def _navigate_aggressively(self):
        """Aggressive navigation using multiple methods"""
        methods = [
            self._navigate_button,
            self._navigate_keyboard,
            self._navigate_javascript,
            self._navigate_swipe
        ]
        
        for method in methods:
            try:
                if method():
                    time.sleep(4)  # Longer wait for complete loading
                    return True
            except Exception as e:
                print(f"Navigation method failed: {e}")
                continue
        
        return False
    
    def _navigate_button(self):
        """Button navigation"""
        selectors = [
            "button[aria-label*='Next']",
            "button[aria-label='Next']",
            "[role='button'][aria-label*='Next']"
        ]
        
        for selector in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                        return True
            except:
                continue
        return False
    
    def _navigate_keyboard(self):
        """Keyboard navigation"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            return True
        except:
            return False
    
    def _navigate_javascript(self):
        """JavaScript navigation"""
        js_commands = [
            "document.querySelector('[aria-label*=\"Next\"]')?.click();",
            "document.body.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true}));"
        ]
        
        for js_cmd in js_commands:
            try:
                self.driver.execute_script(js_cmd)
                return True
            except:
                continue
        return False
    
    def _navigate_swipe(self):
        """Swipe simulation"""
        try:
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            start_x = viewport_width * 0.7
            end_x = viewport_width * 0.3
            y = viewport_height * 0.4
            
            actions = ActionChains(self.driver)
            actions.move_by_offset(start_x, y)
            actions.click_and_hold()
            actions.move_by_offset(end_x - start_x, 0)
            actions.release()
            actions.perform()
            return True
        except:
            return False
    
    def extract_complete_carousel(self, shortcode, output_directory):
        """Extract ALL carousel images using comprehensive analysis"""
        print(f"🎯 COMPLETE CAROUSEL EXTRACTION for {shortcode}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Navigate to post
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔗 Loading: {url}")
        self.driver.get(url)
        time.sleep(8)
        
        # Close popups
        self._close_popups()
        time.sleep(3)
        
        # Collect all unique images through aggressive navigation
        all_discovered_images = {}  # Use dict to store analysis
        navigation_attempts = 0
        max_attempts = 30  # More attempts
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        print(f"🔍 Phase 1: Initial analysis...")
        
        while navigation_attempts < max_attempts and consecutive_failures < max_consecutive_failures:
            # Get all images with analysis
            current_images = self._get_all_images_with_analysis()
            
            new_images_found = 0
            carousel_images_found = 0
            
            for img_data in current_images:
                src = img_data['src']
                
                if src not in all_discovered_images:
                    all_discovered_images[src] = img_data
                    new_images_found += 1
                    
                    # Check if it's likely a carousel image
                    analysis = img_data['analysis']
                    y_pos = img_data['y_position']
                    
                    # Carousel criteria:
                    # 1. URL indicates carousel content
                    # 2. Position in upper part of page
                    # 3. Not obviously suggested content
                    is_likely_carousel = (
                        analysis.get('is_carousel', False) or 
                        (y_pos < 600 and not analysis.get('is_feed', False))
                    )
                    
                    if is_likely_carousel:
                        carousel_images_found += 1
                        print(f"   🎯 Carousel image: {img_data['alt'][:40]}")
                    else:
                        print(f"   📰 Feed/suggested: {img_data['alt'][:40]}")
            
            if new_images_found > 0:
                print(f"🔄 Attempt {navigation_attempts + 1}: +{new_images_found} images ({carousel_images_found} likely carousel)")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
            
            # Try navigation
            if navigation_attempts < max_attempts - 1:  # Don't navigate on last attempt
                if not self._navigate_aggressively():
                    consecutive_failures += 1
            
            navigation_attempts += 1
            
            # Brief pause
            time.sleep(1)
        
        # Filter for carousel images only
        carousel_images = []
        for src, img_data in all_discovered_images.items():
            analysis = img_data['analysis']
            y_pos = img_data['y_position']
            
            # Apply carousel filtering
            is_carousel = (
                analysis.get('is_carousel', False) or 
                (y_pos < 600 and not analysis.get('is_feed', False))
            )
            
            if is_carousel:
                carousel_images.append(img_data)
        
        print(f"\n📊 Analysis complete:")
        print(f"   Total images discovered: {len(all_discovered_images)}")
        print(f"   Carousel images identified: {len(carousel_images)}")
        print(f"   Navigation attempts: {navigation_attempts}")
        
        # Download carousel images
        print(f"\n📥 Downloading carousel images...")
        os.makedirs(output_directory, exist_ok=True)
        
        unique_images = []
        existing_hashes = set()
        
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"complete_{shortcode}_carousel_{i}.jpg"
            filepath = os.path.join(output_directory, filename)
            
            success, img_hash, size = self._download_image(img_data['src'], filepath, existing_hashes)
            if success:
                unique_images.append({
                    'index': i,
                    'url': img_data['src'],
                    'filename': filename,
                    'size': size,
                    'hash': img_hash,
                    'alt': img_data['alt'],
                    'analysis': img_data['analysis']
                })
                print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
        
        duration = time.time() - start_time
        
        # Create comprehensive results
        results = {
            'shortcode': shortcode,
            'total_extracted': len(unique_images),
            'images': unique_images,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': len(unique_images) > 0,
            'navigation_attempts': navigation_attempts,
            'total_images_discovered': len(all_discovered_images),
            'carousel_images_identified': len(carousel_images),
            'extraction_method': 'complete_carousel_analysis',
            'duration_seconds': round(duration, 2)
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, f"complete_results_{shortcode}.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n🎉 COMPLETE EXTRACTION FINISHED")
        print(f"📊 Carousel images: {len(unique_images)}")
        print(f"⏱️ Duration: {duration:.1f}s")
        
        if unique_images:
            print(f"📁 Downloaded carousel images:")
            for img in unique_images:
                print(f"   • {img['filename']} ({img['size']:,} bytes) - {img['alt'][:40]}")
        
        print("=" * 60)
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Test the complete extractor
    extractor = CompleteCarouselExtractor()
    try:
        results = extractor.extract_complete_carousel(
            "C0wmEEKItfR", 
            "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0wmEEKItfR"
        )
        
        expected_carousel_images = 4  # Based on our analysis
        actual_carousel_images = results['total_extracted']
        
        print(f"\n📈 FINAL ASSESSMENT:")
        print(f"   Expected: {expected_carousel_images} carousel images")
        print(f"   Extracted: {actual_carousel_images} carousel images")
        print(f"   Success: {'✅ PERFECT' if actual_carousel_images >= expected_carousel_images else '❌ MISSING IMAGES'}")
        
    finally:
        extractor.close()