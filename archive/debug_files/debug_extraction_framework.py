#!/usr/bin/env python3
"""
Comprehensive debugging framework for Instagram image extraction
No mocking - real-world testing with detailed step-by-step validation
"""

import os
import time
import json
import random
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class InstagramExtractionDebugger:
    """Comprehensive debugging framework for Instagram extraction"""
    
    def __init__(self):
        self.driver = None
        self.debug_data = {}
        
    def setup_browser(self):
        """Setup Chrome browser with anti-detection"""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        options = Options()
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        # Don't disable images - we need to see what's actually loading
        options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser setup complete")
    
    def handle_popups(self, shortcode: str) -> Dict[str, Any]:
        """Handle popups and return detailed info about what was found"""
        popup_info = {
            "cookie_popup": False,
            "login_popup": False,
            "overlay_popup": False,
            "popup_actions": []
        }
        
        print(f"🚪 Checking for popups on {shortcode}...")
        
        # Cookie popup handling
        cookie_selectors = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Allow')]", 
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Accept All')]",
            "//button[@aria-label*='Accept']"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                cookie_button.click()
                popup_info["cookie_popup"] = True
                popup_info["popup_actions"].append(f"Clicked cookie button: {selector}")
                print(f"  🍪 Handled cookie popup")
                time.sleep(1)
                break
            except:
                continue
        
        # Login popup handling
        login_selectors = [
            "//button[@aria-label='Close']",
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Cancel')]"
        ]
        
        for selector in login_selectors:
            try:
                login_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                login_button.click()
                popup_info["login_popup"] = True
                popup_info["popup_actions"].append(f"Closed login popup: {selector}")
                print(f"  ❌ Closed login popup")
                time.sleep(1)
                break
            except:
                continue
        
        return popup_info
    
    def analyze_page_structure(self, shortcode: str) -> Dict[str, Any]:
        """Analyze the page structure in detail"""
        print(f"🔍 Analyzing page structure for {shortcode}...")
        
        structure_info = {
            "total_images": 0,
            "content_images": 0,
            "fbcdn_images": 0,
            "carousel_indicators": [],
            "navigation_buttons": [],
            "all_image_sources": [],
            "content_image_details": [],
            "page_source_length": len(self.driver.page_source)
        }
        
        # Find all images
        all_images = self.driver.find_elements(By.TAG_NAME, "img")
        structure_info["total_images"] = len(all_images)
        
        print(f"  📊 Found {len(all_images)} total images on page")
        
        # Analyze each image
        for i, img in enumerate(all_images):
            try:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                structure_info["all_image_sources"].append({
                    "index": i,
                    "src": src,
                    "alt": alt,
                    "is_fbcdn": "fbcdn.net" in src,
                    "is_content": "t51.29350-15" in src,
                    "is_profile": any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])
                })
                
                if "fbcdn.net" in src:
                    structure_info["fbcdn_images"] += 1
                    
                if "t51.29350-15" in src and not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar']):
                    structure_info["content_images"] += 1
                    structure_info["content_image_details"].append({
                        "index": i,
                        "src": src,
                        "alt": alt,
                        "has_photo_by": "Photo by" in alt,
                        "has_date": any(month in alt for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
                    })
            except Exception as e:
                print(f"    ⚠️ Error analyzing image {i}: {e}")
        
        # Check for carousel indicators
        carousel_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='Previous']", 
            "[aria-label*='Go to']",
            ".coreSpriteCarouselNext",
            ".coreSpriteCarouselPrev"
        ]
        
        for selector in carousel_selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                structure_info["carousel_indicators"].append({
                    "selector": selector,
                    "count": len(elements)
                })
        
        print(f"  📷 Content images: {structure_info['content_images']}")
        print(f"  🎠 Carousel indicators found: {len(structure_info['carousel_indicators'])}")
        
        return structure_info
    
    def test_extraction_consistency(self, shortcode: str, num_runs: int = 3) -> Dict[str, Any]:
        """Test extraction multiple times to check consistency"""
        print(f"🔄 Testing extraction consistency for {shortcode} ({num_runs} runs)...")
        
        consistency_data = {
            "shortcode": shortcode,
            "runs": [],
            "is_consistent": True,
            "variance_detected": False
        }
        
        for run in range(num_runs):
            print(f"\n  Run {run + 1}/{num_runs}...")
            
            # Navigate to post
            url = f"https://www.instagram.com/p/{shortcode}/"
            self.driver.get(url)
            
            # Handle popups
            popup_info = self.handle_popups(shortcode)
            
            # Wait for dynamic content
            print(f"    ⏳ Waiting for content to load...")
            time.sleep(random.uniform(8, 12))
            
            # Analyze structure
            structure = self.analyze_page_structure(shortcode)
            
            run_data = {
                "run_number": run + 1,
                "timestamp": datetime.now().isoformat(),
                "popup_info": popup_info,
                "structure": structure,
                "extracted_urls": []
            }
            
            # Extract content images
            for img_detail in structure["content_image_details"]:
                run_data["extracted_urls"].append(img_detail["src"])
            
            print(f"    ✅ Run {run + 1}: {len(run_data['extracted_urls'])} images extracted")
            
            consistency_data["runs"].append(run_data)
            
            # Check consistency
            if run > 0:
                prev_count = len(consistency_data["runs"][run-1]["extracted_urls"])
                current_count = len(run_data["extracted_urls"])
                if prev_count != current_count:
                    consistency_data["is_consistent"] = False
                    consistency_data["variance_detected"] = True
                    print(f"    ⚠️ INCONSISTENCY: Previous run had {prev_count}, this run has {current_count}")
        
        return consistency_data
    
    def debug_specific_post(self, shortcode: str) -> Dict[str, Any]:
        """Comprehensive debugging for a specific post"""
        print(f"\n🔬 COMPREHENSIVE DEBUG: {shortcode}")
        print("=" * 60)
        
        debug_data = {
            "shortcode": shortcode,
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "timestamp": datetime.now().isoformat(),
            "consistency_test": None,
            "final_analysis": None
        }
        
        # Test consistency
        debug_data["consistency_test"] = self.test_extraction_consistency(shortcode, 3)
        
        # Final analysis
        url = f"https://www.instagram.com/p/{shortcode}/"
        self.driver.get(url)
        self.handle_popups(shortcode)
        time.sleep(10)  # Longer wait for final analysis
        debug_data["final_analysis"] = self.analyze_page_structure(shortcode)
        
        return debug_data
    
    def save_debug_report(self, debug_data: Dict[str, Any], output_dir: str = "debug_reports"):
        """Save detailed debug report"""
        Path(output_dir).mkdir(exist_ok=True)
        
        shortcode = debug_data["shortcode"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/debug_{shortcode}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(debug_data, f, indent=2)
        
        print(f"💾 Debug report saved: {filename}")
        return filename
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main debugging function"""
    # Test posts that showed issues
    problem_posts = ['C0xFHGOrBN7', 'C0wmEEKItfR']
    
    debugger = InstagramExtractionDebugger()
    debugger.setup_browser()
    
    try:
        for shortcode in problem_posts:
            debug_data = debugger.debug_specific_post(shortcode)
            report_file = debugger.save_debug_report(debug_data)
            
            # Print summary
            consistency = debug_data["consistency_test"]
            final = debug_data["final_analysis"]
            
            print(f"\n📋 SUMMARY FOR {shortcode}:")
            print(f"  🔄 Consistency: {'✅ CONSISTENT' if consistency['is_consistent'] else '❌ INCONSISTENT'}")
            print(f"  📷 Content images detected: {final['content_images']}")
            print(f"  🎠 Carousel indicators: {len(final['carousel_indicators'])}")
            
            if consistency['variance_detected']:
                runs = consistency['runs']
                counts = [len(run['extracted_urls']) for run in runs]
                print(f"  ⚠️ Image counts varied: {counts}")
            
            print("-" * 40)
    
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()