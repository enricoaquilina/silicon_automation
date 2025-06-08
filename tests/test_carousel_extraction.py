#!/usr/bin/env python3
"""
Comprehensive test suite for Instagram carousel extraction
Test-driven development without mocking - real browser tests
"""

import pytest
import os
import time
import hashlib
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# Test configuration
TEST_SHORTCODE = "C0xFHGOrBN7"
TEST_OUTPUT_DIR = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
EXPECTED_MIN_IMAGES = 2  # Minimum expected carousel images
EXPECTED_MAX_IMAGES = 10  # Maximum reasonable carousel size


class TestCarouselExtraction:
    """Test suite for carousel image extraction"""
    
    @pytest.fixture(scope="class")
    def browser_setup(self):
        """Setup browser for testing"""
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
        
        yield driver
        driver.quit()
    
    def close_popups(self, driver):
        """Close Instagram popups including cookie consent and login prompts"""
        # First round: Cookie consent
        cookie_patterns = [
            "//button[contains(text(), 'Allow all cookies')]",
            "//button[contains(text(), 'Accept all')]", 
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Allow essential and optional cookies')]"
        ]
        
        for pattern in cookie_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Accepted cookies")
                        time.sleep(3)
                        break
            except:
                continue
        
        # Second round: Login/signup prompts
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
                elements = driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"   ✅ Dismissed login prompt")
                        time.sleep(2)
                        break
            except:
                continue
    
    @pytest.fixture(scope="class")
    def output_directory(self):
        """Ensure output directory exists"""
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        # Note: Don't clean files during testing to allow validation
        return TEST_OUTPUT_DIR
    
    def test_01_browser_can_load_instagram_post(self, browser_setup):
        """Test: Browser can successfully load Instagram post"""
        driver = browser_setup
        url = f"https://www.instagram.com/p/{TEST_SHORTCODE}/"
        
        driver.get(url)
        time.sleep(5)
        
        # Close popups first
        self.close_popups(driver)
        
        # Verify page loaded
        assert "Instagram" in driver.title
        # Verify post content is present
        assert driver.find_elements(By.CSS_SELECTOR, "article, [role='main']")
        
        print(f"✅ Successfully loaded: {url}")
    
    def test_02_can_detect_carousel_post(self, browser_setup):
        """Test: Can detect if post is a carousel (multiple images)"""
        driver = browser_setup
        url = f"https://www.instagram.com/p/{TEST_SHORTCODE}/"
        driver.get(url)
        time.sleep(5)
        
        # Close popups first
        self.close_popups(driver)
        
        # Look for carousel indicators
        carousel_indicators = [
            "button[aria-label*='Next']",
            "[role='button'][aria-label*='Next']", 
            "div[style*='transform: translateX']",  # Carousel container
            ".coreSpriteRightChevron",  # Instagram's next arrow class
        ]
        
        is_carousel = False
        for indicator in carousel_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                is_carousel = True
                break
        
        assert is_carousel, f"Post {TEST_SHORTCODE} should be detected as carousel"
        print(f"✅ Detected carousel post: {TEST_SHORTCODE}")
    
    def test_03_can_find_initial_images(self, browser_setup):
        """Test: Can find initial visible images in carousel"""
        driver = browser_setup
        url = f"https://www.instagram.com/p/{TEST_SHORTCODE}/"
        driver.get(url)
        time.sleep(5)
        
        # Close popups first
        self.close_popups(driver)
        
        # Find images in the post - updated for current Instagram structure
        images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        high_quality_images = [
            img for img in images 
            if img.get_attribute('src') and 
            't51.29350-15' in img.get_attribute('src') and  # High resolution indicator
            not any(exclude in img.get_attribute('src').lower() 
                   for exclude in ['profile', 'avatar', 's150x150', 's320x320', 't51.2885-19'])
        ]
        
        assert len(high_quality_images) >= 1, "Should find at least 1 initial image"
        
        # Test image URLs are valid
        for img in high_quality_images[:3]:  # Test first 3
            src = img.get_attribute('src')
            assert src.startswith('https://'), f"Image URL should be HTTPS: {src}"
            assert any(cdn in src for cdn in ['instagram', 'fbcdn']), f"Should be Instagram CDN URL: {src}"
        
        print(f"✅ Found {len(high_quality_images)} initial images")
    
    def test_04_can_navigate_carousel_next(self, browser_setup):
        """Test: Can successfully navigate to next image in carousel"""
        driver = browser_setup
        url = f"https://www.instagram.com/p/{TEST_SHORTCODE}/"
        driver.get(url)
        time.sleep(5)
        
        # Close popups first
        self.close_popups(driver)
        
        # Get initial image state  
        initial_images = set()
        for img in driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']"):
            src = img.get_attribute('src')
            if src and 't51.29350-15' in src and not any(exclude in src for exclude in ['profile', 'avatar', 't51.2885-19']):
                initial_images.add(src)
        
        # Find and click next button
        next_clicked = False
        next_selectors = [
            "button[aria-label*='Next']",
            "button[aria-label='Next']",
            "[role='button'][aria-label*='Next']",
            "div[role='button'][aria-label*='Next']"
        ]
        
        for selector in next_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    try:
                        # Try ActionChains hover + click first
                        ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
                        next_clicked = True
                    except:
                        try:
                            # Fallback to JavaScript click
                            driver.execute_script("arguments[0].click();", btn)
                            next_clicked = True
                        except:
                            continue
                    
                    if next_clicked:
                        time.sleep(3)
                        break
            if next_clicked:
                break
        
        assert next_clicked, "Should be able to click Next button"
        
        # Verify new images appeared
        after_images = set()
        for img in driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']"):
            src = img.get_attribute('src')
            if src and 't51.29350-15' in src and not any(exclude in src for exclude in ['profile', 'avatar', 't51.2885-19']):
                after_images.add(src)
        
        new_images = after_images - initial_images
        assert len(new_images) > 0, "Navigation should reveal new images"
        
        print(f"✅ Navigation revealed {len(new_images)} new images")
    
    def test_05_can_extract_all_carousel_images(self, browser_setup, output_directory):
        """Test: Can extract ALL images from carousel"""
        from carousel_extractor import CarouselExtractor  # Import our implementation
        
        extractor = CarouselExtractor(browser_setup)
        results = extractor.extract_all_images(TEST_SHORTCODE, output_directory)
        
        # Verify results structure
        assert 'images' in results
        assert 'shortcode' in results
        assert 'total_extracted' in results
        
        # Verify minimum image count
        assert results['total_extracted'] >= EXPECTED_MIN_IMAGES, \
            f"Should extract at least {EXPECTED_MIN_IMAGES} images, got {results['total_extracted']}"
        
        # Verify maximum reasonable count
        assert results['total_extracted'] <= EXPECTED_MAX_IMAGES, \
            f"Extracted too many images ({results['total_extracted']}), possible duplicates"
        
        # Verify all images have unique content
        hashes = set()
        for img_info in results['images']:
            assert 'hash' in img_info
            assert img_info['hash'] not in hashes, f"Duplicate image detected: {img_info['filename']}"
            hashes.add(img_info['hash'])
        
        print(f"✅ Extracted {results['total_extracted']} unique images")
    
    def test_06_downloaded_images_are_valid(self, output_directory):
        """Test: All downloaded images are valid and non-empty"""
        image_files = list(Path(output_directory).glob("test_*.jpg"))
        
        assert len(image_files) >= EXPECTED_MIN_IMAGES, \
            f"Should have at least {EXPECTED_MIN_IMAGES} downloaded images"
        
        for img_file in image_files:
            # Check file size
            size = img_file.stat().st_size
            assert size > 1000, f"Image too small: {img_file.name} ({size} bytes)"
            
            # Check file is valid JPEG
            with open(img_file, 'rb') as f:
                header = f.read(10)
                assert header.startswith(b'\xff\xd8\xff'), f"Invalid JPEG header: {img_file.name}"
        
        print(f"✅ All {len(image_files)} downloaded images are valid")
    
    def test_07_extraction_metadata_is_complete(self, output_directory):
        """Test: Extraction creates complete metadata"""
        metadata_file = Path(output_directory) / "test_extraction_results.json"
        
        assert metadata_file.exists(), "Should create metadata file"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        required_fields = ['shortcode', 'total_extracted', 'images', 'timestamp', 'success']
        for field in required_fields:
            assert field in metadata, f"Metadata missing field: {field}"
        
        # Verify image metadata
        for img_info in metadata['images']:
            required_img_fields = ['filename', 'url', 'size', 'hash', 'index']
            for field in required_img_fields:
                assert field in img_info, f"Image metadata missing field: {field}"
        
        print(f"✅ Complete metadata for {len(metadata['images'])} images")
    
    def test_08_no_duplicate_images_downloaded(self, output_directory):
        """Test: No duplicate images were downloaded"""
        image_files = list(Path(output_directory).glob("test_*.jpg"))
        
        hashes = []
        for img_file in image_files:
            with open(img_file, 'rb') as f:
                content = f.read()
                img_hash = hashlib.md5(content).hexdigest()
                hashes.append(img_hash)
        
        unique_hashes = set(hashes)
        assert len(hashes) == len(unique_hashes), \
            f"Found duplicate images: {len(hashes)} files, {len(unique_hashes)} unique"
        
        print(f"✅ All {len(image_files)} images are unique")
    
    def test_09_extraction_performance_reasonable(self, browser_setup, output_directory):
        """Test: Extraction completes in reasonable time"""
        from carousel_extractor import CarouselExtractor
        
        start_time = time.time()
        extractor = CarouselExtractor(browser_setup)
        results = extractor.extract_all_images(TEST_SHORTCODE, output_directory)
        duration = time.time() - start_time
        
        # Should complete within 2 minutes
        assert duration < 120, f"Extraction took too long: {duration:.1f}s"
        
        # Should be efficient (< 10s per image)
        time_per_image = duration / results['total_extracted']
        assert time_per_image < 10, f"Too slow per image: {time_per_image:.1f}s"
        
        print(f"✅ Extraction completed in {duration:.1f}s ({time_per_image:.1f}s per image)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])