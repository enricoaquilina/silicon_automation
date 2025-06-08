#!/usr/bin/env python3
"""
Instagram Login Extractor
Extract images with Instagram login for better access to post data
"""

import time
import random
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

class InstagramLoginExtractor:
    """Instagram extractor with login capability"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.driver = None
        self.logged_in = False
    
    def setup_browser(self):
        """Setup browser with anti-detection"""
        try:
            options = Options()
            
            # Use realistic user agent
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Anti-detection measures
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Keep cookies and session data
            options.add_argument("--user-data-dir=/tmp/chrome_instagram_session")
            
            # NOT headless for login
            # options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_window_size(1920, 1080)
            
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def login_to_instagram(self):
        """Login to Instagram"""
        try:
            print("🔐 Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            
            # Wait for login page to load
            time.sleep(3)
            
            # Handle cookie banner if present
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass  # No cookie banner
            
            # Find and fill username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
            )
            username_input.clear()
            username_input.send_keys(self.username)
            time.sleep(random.uniform(1, 2))
            
            # Find and fill password
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(random.uniform(1, 2))
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            print("   ⏳ Waiting for login...")
            time.sleep(5)
            
            # Check if login was successful
            if "instagram.com/accounts/login" not in self.driver.current_url:
                print("   ✅ Login successful!")
                self.logged_in = True
                
                # Handle "Save Info" prompt if it appears
                try:
                    not_now_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                    )
                    not_now_button.click()
                    time.sleep(1)
                except:
                    pass
                
                # Handle notification prompt if it appears
                try:
                    not_now_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                    )
                    not_now_button.click()
                    time.sleep(1)
                except:
                    pass
                
                return True
            else:
                print("   ❌ Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    def extract_post_with_login(self, shortcode: str) -> Dict[str, Any]:
        """Extract post data with login access"""
        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"🔍 Extracting (logged in): {url}")
            
            self.driver.get(url)
            time.sleep(5)
            
            result = {
                "shortcode": shortcode,
                "carousel_images": [],
                "post_type": "unknown",
                "success": False,
                "logged_in": self.logged_in
            }
            
            # With login, we should have better access to data
            page_source = self.driver.page_source
            
            # Look for carousel indicators with login
            carousel_count_pattern = r'"edge_sidecar_to_children":{[^}]*"count":(\d+)'
            carousel_match = re.search(carousel_count_pattern, page_source)
            
            if carousel_match:
                carousel_count = int(carousel_match.group(1))
                result["post_type"] = "carousel"
                result["carousel_count"] = carousel_count
                print(f"   📊 Detected carousel with {carousel_count} images")
            else:
                result["post_type"] = "single"
                result["carousel_count"] = 1
                print(f"   📊 Detected single image post")
            
            # Extract main post images with better selectors (logged in)
            main_content_images = []
            
            # Strategy 1: Look for the main article content
            try:
                main_article = self.driver.find_element(By.CSS_SELECTOR, "article")
                img_elements = main_article.find_elements(By.CSS_SELECTOR, "img")
                
                for img in img_elements:
                    src = img.get_attribute("src") or ""
                    alt = img.get_attribute("alt") or ""
                    
                    # Focus on content images, not profile pics or UI
                    if ("fbcdn.net" in src and 
                        "t51.29350-15" in src and 
                        not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile'])):
                        
                        main_content_images.append({
                            "src": src,
                            "alt": alt,
                            "index": len(main_content_images)
                        })
                        
            except Exception as e:
                print(f"   ⚠️ Main article extraction failed: {e}")
            
            # Strategy 2: Use JSON data with login access
            display_url_pattern = r'"display_url":"([^"]+fbcdn\.net[^"]+)"'
            display_urls = re.findall(display_url_pattern, page_source)
            
            for url in display_urls:
                clean_url = url.replace('\\u0026', '&').replace('\\/', '/')
                if (clean_url not in [img["src"] for img in main_content_images] and
                    "t51.29350-15" in clean_url):
                    main_content_images.append({
                        "src": clean_url,
                        "alt": f"Post image {len(main_content_images) + 1}",
                        "index": len(main_content_images),
                        "source": "json_display_url"
                    })
            
            # Limit to expected carousel count
            if result["post_type"] == "carousel" and "carousel_count" in result:
                main_content_images = main_content_images[:result["carousel_count"]]
            else:
                main_content_images = main_content_images[:1]  # Single post
            
            result["carousel_images"] = main_content_images
            result["success"] = len(main_content_images) > 0
            
            print(f"   ✅ Extracted {len(main_content_images)} images")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            result["error"] = str(e)
            return result
    
    def cleanup(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def test_login_extraction():
    """Test extraction with login"""
    
    username = "enriaqui"
    password = "Raemarie123!"
    
    extractor = InstagramLoginExtractor(username, password)
    
    try:
        # Setup browser
        if not extractor.setup_browser():
            return
        
        # Login to Instagram
        if not extractor.login_to_instagram():
            print("❌ Could not login, trying without login...")
            # Continue anyway for testing
        
        # Extract the problematic shortcode
        result = extractor.extract_post_with_login("C0xFHGOrBN7")
        
        print("\\n" + "="*60)
        print("🎯 LOGIN-BASED EXTRACTION RESULTS")
        print("="*60)
        print(f"Shortcode: {result['shortcode']}")
        print(f"Post Type: {result['post_type']}")
        print(f"Logged In: {result['logged_in']}")
        if 'carousel_count' in result:
            print(f"Carousel Count: {result['carousel_count']}")
        print(f"Images Found: {len(result['carousel_images'])}")
        print(f"Success: {result['success']}")
        
        if result['carousel_images']:
            print(f"\\n🖼️  EXTRACTED IMAGES:")
            for i, img in enumerate(result['carousel_images'], 1):
                print(f"   {i}. {img['alt'][:60]}")
                print(f"      {img['src'][:80]}...")
                if 'source' in img:
                    print(f"      Source: {img['source']}")
        
        if result.get('error'):
            print(f"\\n❌ Error: {result['error']}")
        
        # Keep browser open for manual inspection
        input("\\nPress Enter to close browser...")
        
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    test_login_extraction()