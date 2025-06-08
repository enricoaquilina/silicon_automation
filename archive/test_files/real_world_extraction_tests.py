#!/usr/bin/env python3
"""
Real-world extraction tests without mocking
Step-by-step validation of extraction logic improvements
"""

import os
import re
import time
import random
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class RealWorldExtractionTester:
    """Real-world testing framework for extraction logic"""
    
    def __init__(self):
        self.driver = None
        self.test_results = {}
        
    def setup_browser(self):
        """Setup Chrome browser"""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        options = Options()
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
        
    def handle_popups(self):
        """Handle Instagram popups"""
        # Cookie popup
        try:
            cookie_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        # Login popup
        try:
            close_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            close_button.click()
            time.sleep(1)
        except:
            pass
    
    def get_all_content_images(self, shortcode: str) -> List[Dict[str, Any]]:
        """Get all content images with detailed metadata"""
        url = f"https://www.instagram.com/p/{shortcode}/"
        self.driver.get(url)
        self.handle_popups()
        
        # Wait for content to load
        time.sleep(random.uniform(8, 12))
        
        content_images = []
        all_images = self.driver.find_elements(By.TAG_NAME, "img")
        
        for i, img in enumerate(all_images):
            try:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                # Check if this is a content image
                if ("fbcdn.net" in src and 
                    "t51.29350-15" in src and 
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                    
                    content_images.append({
                        "index": i,
                        "src": src,
                        "alt": alt,
                        "has_photo_by": "Photo by" in alt,
                        "extracted_date": self.extract_date_from_alt(alt)
                    })
            except Exception as e:
                continue
        
        return content_images
    
    def extract_date_from_alt(self, alt_text: str) -> str:
        """Extract date from alt text"""
        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
        matches = re.findall(date_pattern, alt_text)
        return matches[0] if matches else "No date"
    
    def detect_carousel_vs_single(self, shortcode: str) -> Dict[str, Any]:
        """Detect if post is carousel or single"""
        # Check for carousel navigation buttons
        carousel_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='Previous']", 
            "[aria-label*='Go to']"
        ]
        
        carousel_indicators = 0
        for selector in carousel_selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            carousel_indicators += len(elements)
        
        is_carousel = carousel_indicators > 0
        
        return {
            "is_carousel": is_carousel,
            "carousel_indicators": carousel_indicators,
            "detection_method": "navigation_buttons"
        }
    
    def test_improved_filtering_logic(self, shortcode: str) -> Dict[str, Any]:
        """Test improved filtering logic for main post vs related posts"""
        print(f"\n🧪 Testing improved filtering for {shortcode}...")
        
        # Get all content images
        content_images = self.get_all_content_images(shortcode)
        detection = self.detect_carousel_vs_single(shortcode)
        
        print(f"  📷 Found {len(content_images)} content images")
        print(f"  🎠 Carousel detected: {detection['is_carousel']}")
        
        # Group by date
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img in content_images:
            date = img["extracted_date"]
            if date != "No date":
                date_groups[date].append(img)
            else:
                no_date_images.append(img)
        
        print(f"  📅 Date groups found: {len(date_groups)}")
        for date, imgs in date_groups.items():
            print(f"    {date}: {len(imgs)} images")
        print(f"  🚫 No date images: {len(no_date_images)}")
        
        # Apply different filtering strategies
        strategies = {
            "original_largest_group": self.filter_largest_date_group(date_groups, no_date_images),
            "most_recent_date": self.filter_most_recent_date(date_groups, no_date_images),
            "first_date_encountered": self.filter_first_date_encountered(date_groups, no_date_images),
            "carousel_aware": self.filter_carousel_aware(date_groups, no_date_images, detection["is_carousel"])
        }
        
        # Test each strategy
        results = {}
        for strategy_name, filtered_images in strategies.items():
            results[strategy_name] = {
                "image_count": len(filtered_images),
                "image_urls": [img["src"] for img in filtered_images],
                "dates_included": list(set([img["extracted_date"] for img in filtered_images if img["extracted_date"] != "No date"]))
            }
            print(f"  🔬 {strategy_name}: {len(filtered_images)} images")
        
        return {
            "shortcode": shortcode,
            "total_content_images": len(content_images),
            "carousel_detection": detection,
            "date_groups": {date: len(imgs) for date, imgs in date_groups.items()},
            "no_date_count": len(no_date_images),
            "strategy_results": results,
            "raw_content_images": content_images
        }
    
    def filter_largest_date_group(self, date_groups: Dict, no_date_images: List) -> List[Dict]:
        """Original logic: largest date group + no-date images"""
        if not date_groups:
            return no_date_images
        
        largest_date = max(date_groups.keys(), key=lambda d: len(date_groups[d]))
        return date_groups[largest_date] + no_date_images
    
    def filter_most_recent_date(self, date_groups: Dict, no_date_images: List) -> List[Dict]:
        """Filter by most recent date"""
        if not date_groups:
            return no_date_images
        
        # Convert dates to comparable format and find most recent
        def date_to_sortable(date_str):
            months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                     "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
            try:
                parts = date_str.split()
                month = months[parts[0]]
                day = int(parts[1].rstrip(','))
                year = int(parts[2])
                return (year, month, day)
            except:
                return (0, 0, 0)  # Fallback
        
        most_recent_date = max(date_groups.keys(), key=date_to_sortable)
        return date_groups[most_recent_date] + no_date_images
    
    def filter_first_date_encountered(self, date_groups: Dict, no_date_images: List) -> List[Dict]:
        """Filter by first date encountered (likely main post)"""
        if not date_groups:
            return no_date_images
        
        # Get first date that appears
        first_date = list(date_groups.keys())[0]
        return date_groups[first_date] + no_date_images
    
    def filter_carousel_aware(self, date_groups: Dict, no_date_images: List, is_carousel: bool) -> List[Dict]:
        """Carousel-aware filtering"""
        if not date_groups:
            return no_date_images
        
        if is_carousel:
            # For carousel, expect multiple images from same date
            # Take the date group with most images, but limit to reasonable carousel size
            largest_date = max(date_groups.keys(), key=lambda d: len(date_groups[d]))
            carousel_images = date_groups[largest_date] + no_date_images
            
            # Limit to reasonable carousel size (Instagram max is typically 10)
            return carousel_images[:10]
        else:
            # For single post, take just the first image from any date
            for date, images in date_groups.items():
                if images:
                    return [images[0]]  # Just first image for single post
            return no_date_images[:1] if no_date_images else []
    
    def run_comprehensive_test(self, test_posts: List[str]) -> Dict[str, Any]:
        """Run comprehensive test on multiple posts"""
        print("🔬 COMPREHENSIVE REAL-WORLD EXTRACTION TEST")
        print("=" * 60)
        
        all_results = {}
        
        for i, shortcode in enumerate(test_posts, 1):
            print(f"\n[{i}/{len(test_posts)}] Testing {shortcode}...")
            try:
                result = self.test_improved_filtering_logic(shortcode)
                all_results[shortcode] = result
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                all_results[shortcode] = {"error": str(e)}
        
        return all_results
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main test function"""
    # Test posts with known issues
    test_posts = [
        'C0xFHGOrBN7',  # Should be 3 images (carousel)
        'C0wmEEKItfR',  # Should be 10 images (carousel) 
        'C0xMpxwKoxb',  # Should be 1 image (single)
        'C0wysT_LC-L',  # Should be 1 image (single)
        'C0xLaimIm1B'   # Should be 1 image (single)
    ]
    
    tester = RealWorldExtractionTester()
    tester.setup_browser()
    
    try:
        results = tester.run_comprehensive_test(test_posts)
        
        # Save results
        import json
        Path("test_results").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"test_results/real_world_test_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n📊 TEST SUMMARY:")
        print("=" * 40)
        
        for shortcode, result in results.items():
            if "error" in result:
                print(f"❌ {shortcode}: ERROR - {result['error']}")
                continue
                
            strategies = result["strategy_results"]
            carousel_detected = result["carousel_detection"]["is_carousel"]
            
            print(f"\n🔗 {shortcode} ({'Carousel' if carousel_detected else 'Single'}):")
            print(f"  📷 Total content images found: {result['total_content_images']}")
            
            for strategy, data in strategies.items():
                count = data["image_count"]
                dates = data["dates_included"]
                print(f"  🔬 {strategy}: {count} images (dates: {dates})")
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()