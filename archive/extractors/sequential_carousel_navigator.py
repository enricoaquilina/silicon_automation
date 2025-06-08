#!/usr/bin/env python3
"""
Sequential Carousel Navigator - Captures ONLY images revealed through step-by-step navigation
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


class SequentialCarouselNavigator:
    """Sequential carousel navigator that captures images through step-by-step navigation"""
    
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
    
    def _find_main_carousel_image(self):
        """Find the main carousel image currently displayed (not suggested content)"""
        # Look for images in the main post area only
        # Use more specific selectors to target the main carousel container
        carousel_selectors = [
            "article img[src*='t51.29350-15']",  # Main article images
            "main article img[src*='fbcdn']",     # Main post images
            "[role='main'] img[src*='t51.29350-15']"  # Main role images
        ]
        
        main_carousel_images = []
        
        for selector in carousel_selectors:
            try:
                images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    try:
                        src = img.get_attribute('src')
                        alt = img.get_attribute('alt') or ''
                        location = img.location
                        
                        # Only include images that are:
                        # 1. High quality (t51.29350-15)
                        # 2. Not profile images (t51.2885-19)
                        # 3. In the upper carousel area (not suggested content below)
                        # 4. Actually visible
                        if (src and 
                            't51.29350-15' in src and 
                            't51.2885-19' not in src and 
                            location['y'] < 400 and  # Much stricter Y position for carousel only
                            img.is_displayed()):
                            
                            main_carousel_images.append({
                                'src': src,
                                'alt': alt,
                                'location': location,
                                'element': img
                            })
                    except:
                        continue
            except:
                continue
        
        # Return the most prominent carousel image (usually the largest/most centered)
        if main_carousel_images:
            # Sort by position - prefer images near the center top
            main_carousel_images.sort(key=lambda x: (x['location']['y'], abs(x['location']['x'] - 500)))
            return main_carousel_images[0]
        
        return None
    
    def _navigate_next_with_verification(self):
        """Navigate to next image and verify it actually changed"""
        print("      🔄 Attempting navigation...")
        
        # Get current main image as reference
        current_image = self._find_main_carousel_image()
        if not current_image:
            print("      ❌ No current image found")
            return False
        
        current_src = current_image['src']
        print(f"      📸 Current image: {current_image['alt'][:40]}")
        
        # Try multiple navigation methods
        navigation_methods = [
            self._navigate_button_precise,
            self._navigate_keyboard_focused,
            self._navigate_javascript_targeted
        ]
        
        for method in navigation_methods:
            try:
                if method():
                    # Wait for potential image change
                    time.sleep(3)
                    
                    # Check if image actually changed
                    new_image = self._find_main_carousel_image()
                    if new_image and new_image['src'] != current_src:
                        print(f"      ✅ Navigation successful: {new_image['alt'][:40]}")
                        return True
                    else:
                        print(f"      ⚠️ Navigation clicked but image didn't change")
                        time.sleep(2)  # Wait a bit more
                        
                        # Check again with longer wait
                        new_image = self._find_main_carousel_image()
                        if new_image and new_image['src'] != current_src:
                            print(f"      ✅ Navigation successful (delayed): {new_image['alt'][:40]}")
                            return True
            except Exception as e:
                print(f"      ❌ Navigation method failed: {str(e)[:50]}")
                continue
        
        print("      ❌ All navigation methods failed")
        return False
    
    def _navigate_button_precise(self):
        """Precise button navigation"""
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
                        # Move to element first, then click
                        ActionChains(self.driver).move_to_element(btn).pause(1).click().perform()
                        return True
            except:
                continue
        return False
    
    def _navigate_keyboard_focused(self):
        """Focused keyboard navigation"""
        try:
            # Focus on the main post area first
            article = self.driver.find_element(By.CSS_SELECTOR, "article, main")
            article.click()  # Focus the carousel
            time.sleep(0.5)
            
            # Send arrow key
            ActionChains(self.driver).send_keys(Keys.ARROW_RIGHT).perform()
            return True
        except:
            return False
    
    def _navigate_javascript_targeted(self):
        """Targeted JavaScript navigation"""
        js_commands = [
            # Focus on main article and send arrow key
            """
            const article = document.querySelector('article, main');
            if (article) {
                article.focus();
                article.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true}));
            }
            """,
            # Try clicking next button via JS
            "document.querySelector('[aria-label*=\"Next\"]')?.click();",
        ]
        
        for js_cmd in js_commands:
            try:
                self.driver.execute_script(js_cmd)
                return True
            except:
                continue
        return False
    
    def extract_sequential_carousel(self, shortcode, output_directory):
        """Extract carousel images through sequential navigation ONLY"""
        print(f"🎯 SEQUENTIAL CAROUSEL EXTRACTION for {shortcode}")
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
        
        # Sequential navigation to capture each carousel image
        carousel_images = []
        max_navigation_attempts = 20
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        print(f"📸 Starting sequential carousel navigation...")
        
        # Capture initial image
        initial_image = self._find_main_carousel_image()
        if initial_image:
            carousel_images.append(initial_image)
            print(f"   1️⃣ Initial image: {initial_image['alt'][:40]}")
        else:
            print("❌ No initial carousel image found")
            return {'total_extracted': 0, 'images': [], 'success': False}
        
        # Navigate through carousel step by step
        for attempt in range(max_navigation_attempts):
            print(f"\n🔄 Navigation attempt {attempt + 1}/{max_navigation_attempts}")
            
            # Try to navigate to next image
            if self._navigate_next_with_verification():
                # Get the new current image
                new_image = self._find_main_carousel_image()
                if new_image:
                    # Check if this is a new unique image
                    existing_srcs = [img['src'] for img in carousel_images]
                    if new_image['src'] not in existing_srcs:
                        carousel_images.append(new_image)
                        print(f"   {len(carousel_images)}️⃣ New image: {new_image['alt'][:40]}")
                        consecutive_failures = 0
                    else:
                        print(f"   🔄 Same image as before (possibly looped back)")
                        consecutive_failures += 1
                else:
                    print(f"   ❌ Navigation succeeded but no image found")
                    consecutive_failures += 1
            else:
                print(f"   ❌ Navigation failed")
                consecutive_failures += 1
            
            # Stop if we've failed too many times in a row
            if consecutive_failures >= max_consecutive_failures:
                print(f"🛑 Stopping after {consecutive_failures} consecutive failures")
                break
            
            # Brief pause between attempts
            time.sleep(2)
        
        print(f"\n📊 Sequential navigation complete:")
        print(f"   Carousel images found: {len(carousel_images)}")
        print(f"   Navigation attempts: {attempt + 1}")
        
        # Download all sequential carousel images
        print(f"\n📥 Downloading sequential carousel images...")
        os.makedirs(output_directory, exist_ok=True)
        
        unique_images = []
        existing_hashes = set()
        
        for i, img_data in enumerate(carousel_images, 1):
            filename = f"sequential_{shortcode}_carousel_{i}.jpg"
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
            'navigation_attempts': attempt + 1,
            'extraction_method': 'sequential_carousel_navigation',
            'duration_seconds': round(duration, 2)
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, f"sequential_results_{shortcode}.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n🎉 SEQUENTIAL EXTRACTION COMPLETE")
        print(f"📊 True carousel images: {len(unique_images)}")
        print(f"⏱️ Duration: {duration:.1f}s")
        
        if unique_images:
            print(f"📁 Sequential carousel images:")
            for img in unique_images:
                print(f"   • {img['filename']} ({img['size']:,} bytes) - {img['alt'][:40]}")
        
        print("=" * 60)
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Test the sequential extractor on both carousels
    test_cases = [
        ("C0xFHGOrBN7", "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"),
        ("C0wmEEKItfR", "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0wmEEKItfR")
    ]
    
    for shortcode, output_dir in test_cases:
        print(f"\n{'='*80}")
        print(f"TESTING SEQUENTIAL EXTRACTION: {shortcode}")
        print(f"{'='*80}")
        
        extractor = SequentialCarouselNavigator()
        try:
            results = extractor.extract_sequential_carousel(shortcode, output_dir)
            
            print(f"\n📈 ASSESSMENT for {shortcode}:")
            print(f"   Images extracted: {results['total_extracted']}")
            print(f"   Success: {'✅ YES' if results['total_extracted'] > 2 else '⚠️ NEEDS MORE' if results['total_extracted'] > 0 else '❌ FAILED'}")
            
        finally:
            extractor.close()
        
        time.sleep(5)  # Brief pause between tests