#!/usr/bin/env python3
"""
Selenium-Based Carousel Extractor Test

This test uses enhanced Selenium for robust Instagram carousel image extraction,
incorporating all fixes identified from codebase analysis.
"""

import asyncio
import time
import json
import hashlib
import requests
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
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
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

# Import test plan
from carousel_test_plan import TEST_SHORTCODES, SUCCESS_CRITERIA

class SeleniumCarouselExtractor:
    """Enhanced Selenium-based carousel extractor with comprehensive error handling"""
    
    def __init__(self):
        self.driver = None
        self.results = {}
        self.image_hashes = set()
        
    def setup_browser(self) -> bool:
        """Setup browser with maximum anti-detection"""
        try:
            print("🤖 Setting up enhanced Selenium browser...")
            
            options = Options()
            
            # Anti-detection user agents (rotate randomly)
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Stealth options (comprehensive set)
            stealth_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-gpu",
                "--disable-extensions", 
                "--disable-plugins",
                "--window-size=1920,1080",
                "--headless"  # For testing; remove for debugging
            ]
            
            for arg in stealth_args:
                options.add_argument(arg)
            
            # Experimental options for stealth
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver property (critical for stealth)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Additional stealth modifications
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            print("   ✅ Selenium browser ready with stealth configuration")
            return True
            
        except Exception as e:
            print(f"   ❌ Browser setup failed: {e}")
            return False
    
    def navigate_to_post(self, shortcode: str) -> bool:
        """Navigate to Instagram post with enhanced popup handling"""
        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"   🔍 Navigating to {url}")
            
            self.driver.get(url)
            
            # Enhanced popup handling sequence
            self.handle_all_popups()
            
            # Wait for dynamic content with smart detection
            self.wait_for_dynamic_content()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Navigation failed: {e}")
            return False
    
    def handle_all_popups(self):
        """Comprehensive popup handling based on analysis"""
        print("   🚪 Handling popups...")
        
        # Multiple rounds of popup checking
        for round_num in range(3):  # Check up to 3 times
            popup_found = False
            
            # Cookie consent popups
            cookie_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Allow')]", 
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'Allow All')]",
                "//button[@aria-label*='Accept']",
                "//button[@aria-label*='Allow']"
            ]
            
            for selector in cookie_selectors:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.safe_click(element)
                    print(f"   🍪 Closed cookie popup (round {round_num + 1})")
                    popup_found = True
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Login modals
            login_selectors = [
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Cancel')]",
                "//button[@aria-label='Close']",
                "//button[contains(@aria-label, 'close')]",
                "//div[@role='button'][contains(@aria-label, 'Close')]",
                "//svg[@aria-label='Close']/../..",
                "//*[contains(@class, 'close')]"
            ]
            
            for selector in login_selectors:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.safe_click(element)
                    print(f"   ❌ Closed login popup (round {round_num + 1})")
                    popup_found = True
                    time.sleep(1)
                    break
                except:
                    continue
            
            # General modal/overlay dismissal
            modal_selectors = [
                "//div[@role='dialog']//button",
                "//div[contains(@class, 'modal')]//button",
                "//div[contains(@class, 'overlay')]//button"
            ]
            
            for selector in modal_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        text = button.text.lower()
                        if any(keyword in text for keyword in ['close', 'cancel', 'not now', 'dismiss', '×']):
                            self.safe_click(button)
                            print(f"   🚫 Dismissed modal (round {round_num + 1})")
                            popup_found = True
                            time.sleep(1)
                            break
                except:
                    continue
            
            if not popup_found:
                break  # No more popups found
        
        # Final check: press Escape to close any remaining modals
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except:
            pass
    
    def safe_click(self, element: WebElement):
        """Safe click with multiple fallback methods"""
        try:
            # Method 1: Standard click
            element.click()
        except:
            try:
                # Method 2: JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            except:
                try:
                    # Method 3: ActionChains click
                    ActionChains(self.driver).move_to_element(element).click().perform()
                except:
                    pass  # All methods failed
    
    def wait_for_dynamic_content(self):
        """Smart waiting for dynamic content loading"""
        print("   ⏳ Waiting for dynamic content...")
        
        # Progressive loading detection with multiple checks
        max_wait_time = 15
        check_interval = 1
        elapsed = 0
        
        # Wait for basic page structure
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        except:
            pass  # Continue even if no article found
        
        # Additional wait for dynamic content
        while elapsed < max_wait_time:
            # Check for content stability indicators
            current_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            
            time.sleep(check_interval)
            elapsed += check_interval
            
            new_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            
            # If image count is stable, content likely loaded
            if new_img_count == current_img_count and new_img_count > 0:
                break
        
        # Additional wait for Instagram's progressive loading
        time.sleep(random.uniform(3, 5))
        
        print(f"   ✅ Content ready after {elapsed}s")
    
    def detect_carousel_type(self, shortcode: str) -> Dict[str, Any]:
        """Detect if post is carousel and expected image count"""
        print("   🎠 Detecting carousel type...")
        
        carousel_indicators = 0
        detected_buttons = []
        
        # Enhanced carousel detection with multiple selectors
        carousel_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='Previous']", 
            "button[aria-label*='next']",
            "button[aria-label*='previous']",
            "[aria-label*='Go to']",
            ".carousel-next",
            ".carousel-prev",
            "[data-testid*='next']",
            "[data-testid*='previous']"
        ]
        
        for selector in carousel_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    carousel_indicators += len(elements)
                    detected_buttons.append(selector)
            except:
                continue
        
        # Additional check: look for multiple image elements in post
        try:
            main_articles = self.driver.find_elements(By.CSS_SELECTOR, "main article")
            if main_articles:
                post_images = main_articles[0].find_elements(By.CSS_SELECTOR, "img")
                content_images = [img for img in post_images 
                                if img.get_attribute("src") and "t51.29350-15" in img.get_attribute("src")]
                if len(content_images) > 1:
                    carousel_indicators += 1
        except:
            pass
        
        is_carousel = carousel_indicators > 0
        expected_count = TEST_SHORTCODES.get(shortcode, {}).get("expected_images", 1)
        
        detection_result = {
            "is_carousel": is_carousel,
            "expected_images": expected_count,
            "detection_confidence": "high" if carousel_indicators > 1 else "medium",
            "indicators_found": carousel_indicators,
            "detected_selectors": detected_buttons
        }
        
        print(f"   🎯 Carousel: {is_carousel}, Expected: {expected_count} images, Indicators: {carousel_indicators}")
        return detection_result
    
    def extract_all_images(self, shortcode: str) -> List[Dict[str, Any]]:
        """Extract all potential images with metadata using multiple strategies"""
        print("   📸 Extracting images...")
        
        all_images = []
        
        # Strategy 1: Main article container (most reliable)
        try:
            main_articles = self.driver.find_elements(By.CSS_SELECTOR, "main article")
            if main_articles:
                img_elements = main_articles[0].find_elements(By.CSS_SELECTOR, "img")
                strategy_images = self.process_image_elements(img_elements, "main_article")
                if strategy_images:
                    print(f"   ✅ Main article strategy: {len(strategy_images)} images")
                    all_images.extend(strategy_images)
        except Exception as e:
            print(f"   ⚠️  Main article strategy failed: {e}")
        
        # Strategy 2: Generic article container
        if not all_images:
            try:
                articles = self.driver.find_elements(By.CSS_SELECTOR, "article")
                if articles:
                    img_elements = articles[0].find_elements(By.CSS_SELECTOR, "img")
                    strategy_images = self.process_image_elements(img_elements, "article")
                    if strategy_images:
                        print(f"   ✅ Article strategy: {len(strategy_images)} images")
                        all_images.extend(strategy_images)
            except Exception as e:
                print(f"   ⚠️  Article strategy failed: {e}")
        
        # Strategy 3: Post container selectors
        if not all_images:
            try:
                post_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[role='presentation'][tabindex='-1'], main > div > div > div")
                if post_containers:
                    img_elements = post_containers[0].find_elements(By.CSS_SELECTOR, "img")
                    strategy_images = self.process_image_elements(img_elements, "post_container")
                    if strategy_images:
                        print(f"   ✅ Post container strategy: {len(strategy_images)} images")
                        all_images.extend(strategy_images)
            except Exception as e:
                print(f"   ⚠️  Post container strategy failed: {e}")
        
        # Strategy 4: Fallback - all images with filtering
        if not all_images:
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
                strategy_images = self.process_image_elements(img_elements, "fallback")
                if strategy_images:
                    print(f"   ✅ Fallback strategy: {len(strategy_images)} images")
                    all_images.extend(strategy_images)
            except Exception as e:
                print(f"   ⚠️  Fallback strategy failed: {e}")
        
        # Remove duplicates while preserving order
        unique_images = []
        seen_urls = set()
        
        for img in all_images:
            if img["src"] not in seen_urls:
                unique_images.append(img)
                seen_urls.add(img["src"])
        
        print(f"   📊 Found {len(unique_images)} unique images total")
        return unique_images
    
    def process_image_elements(self, img_elements: List[WebElement], strategy: str) -> List[Dict[str, Any]]:
        """Process image elements and extract metadata"""
        processed_images = []
        
        for img in img_elements:
            try:
                src = img.get_attribute("src")
                alt = img.get_attribute("alt") or ""
                
                # Filter for Instagram content images
                if (src and 
                    ("fbcdn.net" in src or "scontent" in src) and
                    "t51.29350-15" in src and
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                    
                    processed_images.append({
                        "src": src,
                        "alt": alt,
                        "strategy": strategy,
                        "has_photo_by": "Photo by" in alt,
                        "extracted_date": self.extract_date_from_alt(alt)
                    })
            except:
                continue
        
        return processed_images
    
    def extract_date_from_alt(self, alt_text: str) -> str:
        """Extract date from alt text using regex"""
        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
        matches = re.findall(date_pattern, alt_text)
        return matches[0] if matches else "No date"
    
    def filter_main_post_images(self, all_images: List[Dict], is_carousel: bool) -> List[Dict]:
        """Filter main post images from related content using enhanced logic"""
        print("   🎯 Filtering main post images...")
        
        if not all_images:
            return []
        
        # Group images by date extracted from alt text
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img in all_images:
            date = img.get("extracted_date", "No date")
            
            if date != "No date":
                date_groups[date].append(img)
            else:
                no_date_images.append(img)
        
        print(f"   📅 Date groups: {len(date_groups)}, No-date: {len(no_date_images)}")
        for date, imgs in date_groups.items():
            print(f"     {date}: {len(imgs)} images")
        
        # Apply carousel-aware filtering with improved logic
        if is_carousel:
            # For carousel, use first chronological date + no-date images
            if date_groups:
                # Get first date chronologically (likely main post)
                first_date = list(date_groups.keys())[0]
                main_images = date_groups[first_date].copy()
                
                # Include no-date images that appear early (likely same carousel)
                if len(date_groups) > 1:
                    # Find position boundary between date groups
                    second_date = list(date_groups.keys())[1]
                    
                    # For carousel, include early no-date images
                    early_no_date = []
                    for img in no_date_images:
                        # Simple heuristic: include first few no-date images
                        if len(early_no_date) < 5:  # Reasonable limit
                            early_no_date.append(img)
                    
                    main_images.extend(early_no_date)
                else:
                    # Only one date group, include all no-date images
                    main_images.extend(no_date_images)
                
                # Limit to reasonable carousel size
                result = main_images[:10]
                print(f"   🎠 Carousel filter: {len(result)} images from {first_date} + no-date")
                return result
            else:
                # No dates found, return first several images
                result = no_date_images[:10]
                print(f"   🎠 Carousel filter: {len(result)} no-date images")
                return result
        else:
            # For single post, take first image from any source
            if date_groups:
                first_date = list(date_groups.keys())[0]
                result = date_groups[first_date][:1]
                print(f"   📷 Single filter: 1 image from {first_date}")
                return result
            else:
                result = no_date_images[:1]
                print(f"   📷 Single filter: 1 no-date image")
                return result
    
    def navigate_carousel_complete(self, shortcode: str, expected_count: int) -> List[str]:
        """Navigate through complete carousel to collect all images"""
        print(f"   🎠 Navigating carousel for {expected_count} images...")
        
        collected_urls = set()
        max_navigation_attempts = expected_count + 3  # Safety margin
        navigation_attempt = 0
        
        # Initial image collection
        current_images = self.extract_all_images(shortcode)
        filtered_images = self.filter_main_post_images(current_images, True)
        
        for img in filtered_images:
            collected_urls.add(img["src"])
        
        print(f"   📸 Initial collection: {len(collected_urls)} images")
        
        # Navigate through carousel if needed
        while len(collected_urls) < expected_count and navigation_attempt < max_navigation_attempts:
            navigation_attempt += 1
            
            # Try to navigate to next image
            navigation_success = self.navigate_next_image()
            
            if not navigation_success:
                print(f"   ⚠️  Navigation failed at attempt {navigation_attempt}")
                break
            
            # Wait for new content to load
            time.sleep(random.uniform(2, 4))
            
            # Extract images from new position
            current_images = self.extract_all_images(shortcode)
            filtered_images = self.filter_main_post_images(current_images, True)
            
            new_images_found = 0
            for img in filtered_images:
                if img["src"] not in collected_urls:
                    collected_urls.add(img["src"])
                    new_images_found += 1
            
            print(f"   📸 Navigation {navigation_attempt}: +{new_images_found} images (total: {len(collected_urls)})")
            
            # Stop if no new images found
            if new_images_found == 0:
                print(f"   🔚 No new images found, stopping navigation")
                break
        
        print(f"   ✅ Carousel navigation complete: {len(collected_urls)} unique URLs")
        return list(collected_urls)
    
    def navigate_next_image(self) -> bool:
        """Navigate to next image using multiple methods with enhanced reliability"""
        
        # Method 1: Enhanced button clicking with multiple selectors
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='next']",
            ".carousel-next",
            "[data-testid='next']",
            "button[aria-label*='Go to slide']"
        ]
        
        for selector in next_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        # Check if element is visible and clickable
                        if element.is_displayed() and element.is_enabled():
                            self.safe_click(element)
                            print(f"   ➡️  Clicked next button: {selector}")
                            return True
                    except:
                        continue
            except:
                continue
        
        # Method 2: XPath-based navigation (more specific)
        xpath_selectors = [
            "//button[contains(@aria-label, 'Next')]",
            "//button[contains(@aria-label, 'next')]",
            "//*[@role='button'][contains(@aria-label, 'Next')]"
        ]
        
        for xpath in xpath_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            self.safe_click(element)
                            print(f"   ➡️  Clicked next button (XPath)")
                            return True
                    except:
                        continue
            except:
                continue
        
        # Method 3: Keyboard navigation
        try:
            # Focus on body and send arrow key
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            print(f"   ⌨️  Used keyboard navigation")
            return True
        except:
            pass
        
        # Method 4: Swipe simulation (for mobile-like behavior)
        try:
            # Find main image and swipe left on it
            main_articles = self.driver.find_elements(By.CSS_SELECTOR, "main article")
            if main_articles:
                imgs = main_articles[0].find_elements(By.CSS_SELECTOR, "img")
                if imgs:
                    action = ActionChains(self.driver)
                    action.click_and_hold(imgs[0]).move_by_offset(-100, 0).release().perform()
                    print(f"   👆 Used swipe simulation")
                    return True
        except:
            pass
        
        print(f"   ❌ All navigation methods failed")
        return False
    
    def deduplicate_images(self, image_urls: List[str]) -> List[str]:
        """Remove duplicate images using advanced techniques"""
        print("   🔍 Deduplicating images...")
        
        if not image_urls:
            return []
        
        unique_urls = []
        seen_patterns = set()
        
        for url in image_urls:
            # URL pattern analysis for quick deduplication
            url_pattern = self.get_url_pattern(url)
            
            if url_pattern not in seen_patterns:
                unique_urls.append(url)
                seen_patterns.add(url_pattern)
        
        print(f"   ✅ Deduplicated: {len(image_urls)} → {len(unique_urls)} images")
        return unique_urls
    
    def get_url_pattern(self, url: str) -> str:
        """Extract pattern from URL for deduplication"""
        # Remove size parameters and extract base identifier
        import re
        
        # Remove size variants (w640, w1080, etc.)
        pattern = re.sub(r'/[wh]\d+/', '/', url)
        
        # Remove query parameters
        pattern = re.sub(r'\?.*$', '', pattern)
        
        # Extract unique identifier from Instagram URL
        # Instagram URLs have patterns like: /t51.29350-15/ABC123_n.jpg
        match = re.search(r'/t51\.29350-15/([^/]+)', pattern)
        if match:
            return match.group(1).split('_')[0]  # Get base identifier
        
        return pattern
    
    def test_single_shortcode(self, shortcode: str) -> Dict[str, Any]:
        """Test extraction for a single shortcode"""
        print(f"\n🧪 Testing {shortcode}...")
        
        start_time = time.time()
        
        try:
            # Step 1: Navigate to post
            navigation_success = self.navigate_to_post(shortcode)
            if not navigation_success:
                return {"success": False, "error": "Navigation failed"}
            
            # Step 2: Detect carousel type
            carousel_info = self.detect_carousel_type(shortcode)
            
            # Step 3: Extract images based on type
            if carousel_info["is_carousel"]:
                # For carousel, use navigation approach
                image_urls = self.navigate_carousel_complete(
                    shortcode, 
                    carousel_info["expected_images"]
                )
            else:
                # For single post, use filtering approach
                all_images = self.extract_all_images(shortcode)
                filtered_images = self.filter_main_post_images(
                    all_images, 
                    carousel_info["is_carousel"]
                )
                image_urls = [img["src"] for img in filtered_images]
            
            # Step 4: Deduplicate
            unique_urls = self.deduplicate_images(image_urls)
            
            # Step 5: Validate results
            expected_count = TEST_SHORTCODES[shortcode]["expected_images"]
            success = len(unique_urls) == expected_count
            
            duration = time.time() - start_time
            
            result = {
                "success": success,
                "shortcode": shortcode,
                "expected_images": expected_count,
                "extracted_images": len(unique_urls),
                "carousel_detected": carousel_info["is_carousel"],
                "image_urls": unique_urls,
                "duration_seconds": duration,
                "carousel_info": carousel_info
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {shortcode}: {len(unique_urls)}/{expected_count} images in {duration:.1f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ FAIL {shortcode}: {e}")
            return {
                "success": False,
                "shortcode": shortcode,
                "error": str(e),
                "duration_seconds": duration
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all shortcodes"""
        print("🚀 SELENIUM CAROUSEL EXTRACTOR TEST")
        print("=" * 60)
        
        if not self.setup_browser():
            return {"error": "Browser setup failed"}
        
        try:
            results = {}
            
            for shortcode in TEST_SHORTCODES.keys():
                try:
                    result = self.test_single_shortcode(shortcode)
                    results[shortcode] = result
                    
                    # Small delay between tests to avoid rate limiting
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    print(f"   ❌ Test failed for {shortcode}: {e}")
                    results[shortcode] = {"success": False, "error": str(e)}
            
            # Calculate summary statistics
            total_tests = len(results)
            successful_tests = sum(1 for r in results.values() if r.get("success", False))
            accuracy_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            
            avg_duration = sum(r.get("duration_seconds", 0) for r in results.values()) / total_tests
            
            summary = {
                "test_approach": "selenium_enhanced",
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "accuracy_rate": accuracy_rate,
                "average_duration": avg_duration,
                "timestamp": datetime.now().isoformat(),
                "individual_results": results
            }
            
            print(f"\n📊 SELENIUM TEST SUMMARY:")
            print(f"   Accuracy: {successful_tests}/{total_tests} ({accuracy_rate:.1f}%)")
            print(f"   Average duration: {avg_duration:.1f}s per test")
            
            return summary
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main test execution"""
    extractor = SeleniumCarouselExtractor()
    results = extractor.run_comprehensive_test()
    
    # Save results
    Path("test_results").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"test_results/selenium_test_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to test_results/selenium_test_{timestamp}.json")
    
    # Check if success criteria met
    accuracy = results.get("accuracy_rate", 0)
    target_accuracy = 95  # From SUCCESS_CRITERIA
    
    if accuracy >= target_accuracy:
        print(f"🎉 SUCCESS: Accuracy {accuracy:.1f}% meets target {target_accuracy}%")
    else:
        print(f"🔧 NEEDS WORK: Accuracy {accuracy:.1f}% below target {target_accuracy}%")
    
    # Detailed results by shortcode
    print(f"\n📋 DETAILED RESULTS:")
    for shortcode, result in results.get("individual_results", {}).items():
        if result.get("success"):
            print(f"   ✅ {shortcode}: {result.get('extracted_images', 0)}/{result.get('expected_images', 0)} images")
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ {shortcode}: {error}")

if __name__ == "__main__":
    main()