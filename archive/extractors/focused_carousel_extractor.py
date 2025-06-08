#!/usr/bin/env python3
"""
Focused Carousel Extractor - Only extracts actual carousel images, not suggested content
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


class FocusedCarouselExtractor:
    """Focused carousel image extractor that filters out suggested content"""
    
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
        # Cookie consent
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
                        break
            except:
                continue
        
        # Login prompts
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
    
    def _find_carousel_images_focused(self):
        """Find ONLY carousel images, filtering out suggested content"""
        # Get all high-quality images
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        potential_carousel_images = []
        for img in images:
            try:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                
                # Filter for high-quality post images only
                if (src and 
                    't51.29350-15' in src and  # High resolution post images
                    't51.2885-19' not in src and  # Profile images
                    img.is_displayed()):
                    
                    location = img.location
                    
                    potential_carousel_images.append({
                        'src': src,
                        'alt': alt,
                        'location': location,
                        'y_position': location['y'],
                        'element': img
                    })
            except:
                continue
        
        if not potential_carousel_images:
            return []
        
        # Sort by Y position
        potential_carousel_images.sort(key=lambda x: x['y_position'])
        
        # Group images by Y position proximity (within 200px)
        groups = []
        current_group = [potential_carousel_images[0]]
        
        for img in potential_carousel_images[1:]:
            if abs(img['y_position'] - current_group[-1]['y_position']) < 200:
                current_group.append(img)
            else:
                groups.append(current_group)
                current_group = [img]
        
        if current_group:
            groups.append(current_group)
        
        print(f"📊 Found {len(groups)} position groups:")
        for i, group in enumerate(groups):
            y_range = f"{min(img['y_position'] for img in group)}-{max(img['y_position'] for img in group)}"
            print(f"   Group {i+1}: {len(group)} images at Y {y_range}")
        
        # The first group (topmost) is the actual carousel
        if groups:
            carousel_group = groups[0]
            print(f"🎯 Selected Group 1 as carousel: {len(carousel_group)} images")
            
            # Further filtering: ensure these are actually in the main post
            filtered_carousel = []
            for img_data in carousel_group:
                img = img_data['element']
                
                # Additional checks to ensure it's main post content
                try:
                    # Check if image is within the main article/post container
                    main_containers = self.driver.find_elements(By.CSS_SELECTOR, "main article, [role='main'] article")
                    is_in_main = False
                    
                    if main_containers:
                        main_container = main_containers[0]
                        main_location = main_container.location
                        main_size = main_container.size
                        
                        img_location = img_data['location']
                        
                        # Check if image is within main container bounds
                        if (img_location['y'] >= main_location['y'] and 
                            img_location['y'] <= main_location['y'] + main_size['height'] and
                            img_location['x'] >= main_location['x'] and
                            img_location['x'] <= main_location['x'] + main_size['width']):
                            is_in_main = True
                    
                    # If we can't determine main container, use Y position heuristic
                    # Carousel images should be in upper part of page (Y < 500)
                    if not main_containers and img_data['y_position'] < 500:
                        is_in_main = True
                    
                    if is_in_main:
                        filtered_carousel.append(img_data)
                        
                except Exception as e:
                    # If checks fail, include it (conservative approach)
                    filtered_carousel.append(img_data)
            
            print(f"✅ Final carousel images after filtering: {len(filtered_carousel)}")
            return filtered_carousel
        
        return []
    
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
                        try:
                            ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                        except:
                            try:
                                btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", btn)
                        
                        time.sleep(3)
                        return True
            except:
                continue
        
        return False
    
    def extract_carousel_images(self, shortcode, output_directory):
        """Extract ONLY carousel images, excluding suggested content"""
        print(f"🎯 Focused extraction for {shortcode}")
        
        # Navigate to post
        url = f"https://www.instagram.com/p/{shortcode}/"
        self.driver.get(url)
        time.sleep(8)
        
        # Close popups
        self._close_popups()
        time.sleep(3)
        
        # Get all unique carousel images through navigation
        all_carousel_urls = set()
        navigation_attempts = 0
        max_attempts = 10
        
        # Get initial carousel images (focused)
        initial_images = self._find_carousel_images_focused()
        for img in initial_images:
            all_carousel_urls.add(img['src'])
        
        print(f"📊 Found {len(initial_images)} initial carousel images")
        
        # Navigate through carousel to find more
        while navigation_attempts < max_attempts:
            before_count = len(all_carousel_urls)
            
            if self._navigate_next():
                # Check for new carousel images only
                current_images = self._find_carousel_images_focused()
                new_images = 0
                
                for img in current_images:
                    if img['src'] not in all_carousel_urls:
                        all_carousel_urls.add(img['src'])
                        new_images += 1
                
                if new_images == 0:
                    print(f"🛑 No new carousel images found, stopping navigation")
                    break
                else:
                    print(f"➡️ Navigation {navigation_attempts + 1}: +{new_images} carousel images")
            else:
                print(f"❌ Navigation failed at attempt {navigation_attempts + 1}")
                break
            
            navigation_attempts += 1
        
        print(f"📋 Total unique carousel URLs: {len(all_carousel_urls)}")
        
        # Download only carousel images
        os.makedirs(output_directory, exist_ok=True)
        unique_images = []
        existing_hashes = set()
        
        for i, img_url in enumerate(all_carousel_urls, 1):
            filename = f"carousel_{shortcode}_image_{i}.jpg"
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
            'navigation_attempts': navigation_attempts,
            'extraction_method': 'focused_carousel_only'
        }
        
        # Save metadata
        results_path = os.path.join(output_directory, "focused_extraction_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"🎯 Focused extraction complete: {len(unique_images)} carousel images only")
        return results
    
    def close(self):
        """Close browser if we created it"""
        if self.should_close_driver and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Test the focused extractor
    extractor = FocusedCarouselExtractor()
    try:
        results = extractor.extract_carousel_images(
            "C0xFHGOrBN7", 
            "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
        )
        print(f"🎉 Results: {results['total_extracted']} carousel images extracted")
        
        if results['images']:
            print(f"📁 Carousel images:")
            for img in results['images']:
                print(f"  {img['index']}. {img['filename']} ({img['size']} bytes)")
        
    finally:
        extractor.close()