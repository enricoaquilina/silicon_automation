#!/usr/bin/env python3
"""
Ultimate Carousel Navigator - Aggressive multi-method navigation to find ALL carousel images
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


class UltimateCarouselNavigator:
    """Ultimate carousel extractor with aggressive navigation strategies"""
    
    def __init__(self, driver=None):
        """Initialize with optional existing driver"""
        self.driver = driver
        self.should_close_driver = False
        
        if not self.driver:
            self.driver = self._setup_browser()
            self.should_close_driver = True
    
    def _setup_browser(self):
        """Setup browser with maximum compatibility"""
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
    
    def _get_carousel_images(self):
        """Get current carousel images with position filtering"""
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        carousel_images = []
        for img in images:
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                if (src and 
                    't51.29350-15' in src and 
                    't51.2885-19' not in src and 
                    img.is_displayed()):
                    
                    location = img.location
                    
                    # Only include images in carousel area (top of page)
                    if location['y'] < 600:
                        carousel_images.append({
                            'src': src,
                            'alt': alt,
                            'location': location
                        })
            except:
                continue
        
        return carousel_images
    
    def _try_button_navigation(self):
        """Try button-based navigation with fresh element lookup"""
        print("   🔘 Trying button navigation...")
        
        # Fresh lookup of navigation buttons
        selectors = [
            "button[aria-label*='Next']",
            "button[aria-label='Next']",
            "[role='button'][aria-label*='Next']"
        ]
        
        for selector in selectors:
            try:
                # Get fresh elements each time
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            # Try ActionChains first (most reliable for Instagram)
                            ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                            print("      ✅ Button navigation succeeded")
                            return True
                        except:
                            try:
                                # Fallback to JavaScript click
                                self.driver.execute_script("arguments[0].click();", btn)
                                print("      ✅ JavaScript button click succeeded")
                                return True
                            except:
                                continue
            except:
                continue
        
        print("      ❌ Button navigation failed")
        return False
    
    def _try_keyboard_navigation(self):
        """Try keyboard navigation"""
        print("   ⌨️ Trying keyboard navigation...")
        
        try:
            # Focus on body and send arrow key
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            print("      ✅ Keyboard navigation succeeded")
            return True
        except Exception as e:
            print(f"      ❌ Keyboard navigation failed: {e}")
            return False
    
    def _try_swipe_simulation(self):
        """Try swipe simulation using ActionChains"""
        print("   👆 Trying swipe simulation...")
        
        try:
            # Find the main image area
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Calculate swipe coordinates (middle of viewport)
            start_x = viewport_width * 0.7
            end_x = viewport_width * 0.3
            y = viewport_height * 0.4
            
            # Perform swipe-like drag
            actions = ActionChains(self.driver)
            actions.move_by_offset(start_x, y)
            actions.click_and_hold()
            actions.move_by_offset(end_x - start_x, 0)
            actions.release()
            actions.perform()
            
            print("      ✅ Swipe simulation succeeded")
            return True
        except Exception as e:
            print(f"      ❌ Swipe simulation failed: {e}")
            return False
    
    def _try_javascript_navigation(self):
        """Try JavaScript-based navigation"""
        print("   🔧 Trying JavaScript navigation...")
        
        js_methods = [
            # Try to trigger carousel navigation events
            "document.querySelector('[aria-label*=\"Next\"]')?.click();",
            "document.querySelector('button[aria-label*=\"Next\"]')?.dispatchEvent(new Event('click', {bubbles: true}));",
            # Try keyboard events
            "document.body.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true}));",
            # Try swipe events
            """
            const carousel = document.querySelector('article');
            if (carousel) {
                carousel.dispatchEvent(new TouchEvent('touchstart', {
                    touches: [{clientX: 500, clientY: 300}],
                    bubbles: true
                }));
                carousel.dispatchEvent(new TouchEvent('touchend', {
                    touches: [{clientX: 200, clientY: 300}],
                    bubbles: true
                }));
            }
            """
        ]
        
        for i, js_code in enumerate(js_methods):
            try:
                self.driver.execute_script(js_code)
                print(f"      ✅ JavaScript method {i+1} executed")
                time.sleep(1)  # Give time for effect
                return True
            except Exception as e:
                print(f"      ❌ JavaScript method {i+1} failed: {str(e)[:50]}")
                continue
        
        return False
    
    def _navigate_with_multiple_strategies(self):
        """Try multiple navigation strategies"""
        strategies = [
            self._try_button_navigation,
            self._try_keyboard_navigation,
            self._try_swipe_simulation,
            self._try_javascript_navigation
        ]
        
        for strategy in strategies:
            if strategy():
                time.sleep(3)  # Wait for navigation to complete
                return True
        
        return False
    
    def extract_all_carousel_images(self, shortcode, output_directory):
        """Extract ALL carousel images using aggressive navigation"""
        print(f"🚀 ULTIMATE CAROUSEL EXTRACTION for {shortcode}")
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
        
        # Collect all unique carousel images
        all_carousel_urls = set()
        navigation_attempts = 0
        max_attempts = 25  # Increased attempts
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        # Get initial images
        print(f"📸 Getting initial carousel images...")
        initial_images = self._get_carousel_images()
        for img in initial_images:
            all_carousel_urls.add(img['src'])
        
        print(f"   Found {len(initial_images)} initial images")
        
        # Aggressive navigation loop
        print(f"🔄 Starting aggressive navigation...")
        while navigation_attempts < max_attempts and consecutive_failures < max_consecutive_failures:
            print(f"\n🎯 Navigation attempt {navigation_attempts + 1}/{max_attempts}")
            
            before_count = len(all_carousel_urls)
            
            # Try navigation
            if self._navigate_with_multiple_strategies():
                # Check for new images
                current_images = self._get_carousel_images()
                new_images = 0
                
                for img in current_images:
                    if img['src'] not in all_carousel_urls:
                        all_carousel_urls.add(img['src'])
                        new_images += 1
                        print(f"      🆕 Found new image: {img['alt'][:40]}")
                
                if new_images > 0:
                    print(f"   ✅ Navigation successful: +{new_images} images")
                    consecutive_failures = 0  # Reset failure counter
                else:
                    print(f"   ⚠️ Navigation clicked but no new images")
                    consecutive_failures += 1
            else:
                print(f"   ❌ All navigation methods failed")
                consecutive_failures += 1
            
            navigation_attempts += 1
            
            # Brief pause between attempts
            time.sleep(2)
        
        print(f"\n📋 Navigation complete: {len(all_carousel_urls)} total images found")
        print(f"   Attempts: {navigation_attempts}")
        print(f"   Consecutive failures: {consecutive_failures}")
        
        # Download all images
        print(f"📥 Downloading carousel images...")
        os.makedirs(output_directory, exist_ok=True)
        
        unique_images = []
        existing_hashes = set()
        
        for i, img_url in enumerate(all_carousel_urls, 1):
            filename = f"ultimate_{shortcode}_image_{i}.jpg"
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
                print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
        
        duration = time.time() - start_time
        
        # Create results
        results = {
            'shortcode': shortcode,
            'total_extracted': len(unique_images),
            'images': unique_images,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': len(unique_images) > 0,
            'navigation_attempts': navigation_attempts,
            'initial_images_found': len(initial_images),
            'extraction_method': 'ultimate_aggressive_navigation',
            'duration_seconds': round(duration, 2),
            'performance': {
                'images_per_second': round(len(unique_images) / duration, 2) if duration > 0 else 0
            }
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, f"ultimate_results_{shortcode}.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n🎉 ULTIMATE EXTRACTION COMPLETE")
        print(f"📊 Results: {len(unique_images)} carousel images")
        print(f"⏱️ Duration: {duration:.1f}s")
        print(f"🎯 Expected vs Actual: Need to verify if this is all images")
        
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
    # Test the ultimate extractor
    extractor = UltimateCarouselNavigator()
    try:
        # Test on the problematic carousel
        results = extractor.extract_all_carousel_images(
            "C0xFHGOrBN7", 
            "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
        )
        
        print(f"\n📈 Final Assessment:")
        print(f"   Images extracted: {results['total_extracted']}")
        print(f"   Success: {'YES' if results['total_extracted'] >= 3 else 'NEEDS MORE WORK'}")
        
    finally:
        extractor.close()