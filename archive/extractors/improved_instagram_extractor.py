#!/usr/bin/env python3
"""
Improved Instagram Extractor
Focus on extracting actual carousel images in correct order
"""

import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

class ImprovedInstagramExtractor:
    """Enhanced extractor focused on carousel detection and proper image ordering"""
    
    def __init__(self):
        self.driver = None
    
    def setup_browser(self):
        """Setup browser with anti-detection"""
        try:
            options = Options()
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_window_size(1920, 1080)
            
            return True
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def extract_carousel_info(self, shortcode: str) -> Dict[str, Any]:
        """Extract carousel information and proper image order"""
        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"🔍 Loading: {url}")
            self.driver.get(url)
            
            # Wait for page load
            time.sleep(8)
            
            result = {
                "shortcode": shortcode,
                "post_type": "unknown",
                "carousel_count": 0,
                "main_images": [],
                "all_images": [],
                "success": False
            }
            
            # Get page source for analysis
            page_source = self.driver.page_source
            
            # Strategy 1: Look for carousel indicators in page source
            # Instagram uses JSON-LD or GraphQL data embedded in the page
            carousel_patterns = [
                r'"edge_sidecar_to_children":{[^}]*"count":(\d+)',
                r'"__typename":"GraphSidecar"[^}]*"edge_sidecar_to_children":{[^}]*"count":(\d+)',
                r'sidecar.*?"count":(\d+)'
            ]
            
            for pattern in carousel_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    result["carousel_count"] = int(matches[0])
                    result["post_type"] = "carousel"
                    print(f"   📊 Detected carousel with {result['carousel_count']} images")
                    break
            
            # Strategy 2: Look for main content images with specific patterns
            # Focus on the actual content images, not thumbnails or profile pics
            main_image_patterns = [
                # High-res content images (typically the main carousel images)
                r'"display_url":"([^"]+fbcdn\.net[^"]+)"',
                r'"src":"([^"]+fbcdn\.net[^"]*t51\.29350-15[^"]*p1080x1080[^"]*)"'
            ]
            
            unique_main_images = set()
            
            for pattern in main_image_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    clean_url = match.replace('\\u0026', '&').replace('\\/', '/')
                    
                    # Filter for main content images (not profile pics or UI elements)
                    if all([
                        "fbcdn.net" in clean_url,
                        "t51.29350-15" in clean_url,  # Content image identifier
                        any(ext in clean_url for ext in ['.jpg', '.jpeg', '.webp']),
                        "p1080x1080" in clean_url or "p640x640" in clean_url,  # High-res indicators
                        not any(exclude in clean_url for exclude in ['s150x150', 's320x320', 'profile'])  # Exclude thumbnails/profiles
                    ]):
                        unique_main_images.add(clean_url)
            
            result["main_images"] = list(unique_main_images)
            
            # Strategy 3: Extract ALL images for comparison
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
                for img in img_elements:
                    src = img.get_attribute("src")
                    if src and "fbcdn.net" in src:
                        result["all_images"].append({
                            "src": src,
                            "alt": img.get_attribute("alt") or "",
                            "sizes": img.get_attribute("sizes") or ""
                        })
            except Exception as e:
                print(f"   ⚠️ Element extraction failed: {e}")
            
            # Validation
            if result["post_type"] == "carousel" and result["carousel_count"] > 0:
                expected = result["carousel_count"]
                found = len(result["main_images"])
                print(f"   📊 Expected: {expected} images, Found: {found} main images")
                
                if found >= expected:
                    result["success"] = True
                    # Take only the expected number of images
                    result["main_images"] = result["main_images"][:expected]
                else:
                    print(f"   ⚠️ Missing images! Expected {expected}, found {found}")
            else:
                # Single image post
                if len(result["main_images"]) >= 1:
                    result["post_type"] = "single"
                    result["carousel_count"] = 1
                    result["main_images"] = result["main_images"][:1]
                    result["success"] = True
            
            print(f"   ✅ Analysis complete: {result['post_type']} with {len(result['main_images'])} main images")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            result["error"] = str(e)
            return result
    
    def cleanup(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def test_improved_extraction():
    """Test the improved extraction on our problematic shortcode"""
    
    extractor = ImprovedInstagramExtractor()
    
    try:
        if not extractor.setup_browser():
            return
        
        # Test on the shortcode that had issues
        result = extractor.extract_carousel_info("C0xFHGOrBN7")
        
        print("\n" + "="*60)
        print("🎯 IMPROVED EXTRACTION RESULTS")
        print("="*60)
        print(f"Shortcode: {result['shortcode']}")
        print(f"Post Type: {result['post_type']}")
        print(f"Carousel Count: {result['carousel_count']}")
        print(f"Main Images Found: {len(result['main_images'])}")
        print(f"Total Images on Page: {len(result['all_images'])}")
        print(f"Success: {result['success']}")
        
        if result['main_images']:
            print(f"\n📸 Main Images:")
            for i, img_url in enumerate(result['main_images'], 1):
                print(f"   {i}. {img_url[:80]}...")
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
        
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    test_improved_extraction()