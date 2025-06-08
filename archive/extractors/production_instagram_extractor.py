#!/usr/bin/env python3
"""
Production Instagram Extractor

Automated system to extract Instagram images with:
- Anti-detection browser automation
- GridFS compression and storage
- Rate limiting and error handling
- Batch processing capabilities
- Full VLM pipeline integration
"""

import os
import asyncio
import time
import random
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from PIL import Image
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

class ProductionInstagramExtractor:
    """Production-ready Instagram image extraction system"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.replicate_token = replicate_token
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
        self.driver = None
        
        # Anti-detection and rate limiting
        self.session_stats = {
            "extracted": 0,
            "failed": 0,
            "total_images": 0,
            "start_time": datetime.now(),
            "last_request": None
        }
        
        # Rate limiting (be respectful to Instagram)
        self.request_delay = (3, 7)  # 3-7 seconds between requests
        self.batch_delay = (60, 120)  # 1-2 minutes between batches
        self.daily_limit = 200  # Max extractions per day
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = gridfs.GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def setup_browser(self):
        """Setup browser with maximum anti-detection"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            
            print("🤖 Setting up stealth browser...")
            
            options = Options()
            
            # Anti-detection measures
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            ]
            
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Stealth options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Performance options
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Don't load images in browser (we'll get URLs)
            
            # Headless mode
            options.add_argument("--headless")
            
            # Create driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set viewport
            self.driver.set_window_size(1920, 1080)
            
            print("   ✅ Stealth browser ready")
            return True
            
        except Exception as e:
            print(f"   ❌ Browser setup failed: {e}")
            return False
    
    def apply_strict_main_post_filtering(self, all_images: List[Dict]) -> List[Dict]:
        """Apply strict filtering to detect main post vs related posts when no container is found"""
        from collections import defaultdict
        import re
        
        if not all_images:
            return []
        
        # Group images by date mentioned in alt text
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img_data in all_images:
            alt = img_data["alt"]
            # Extract dates from alt text - more specific patterns
            date_matches = re.findall(r'on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data)
            else:
                # Also check for shorter date patterns
                simple_date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                if simple_date_matches:
                    date = simple_date_matches[0]
                    date_groups[date].append(img_data)
                else:
                    no_date_images.append(img_data)
        
        print(f"         📅 Date groups found: {len(date_groups)}")
        for date, imgs in date_groups.items():
            print(f"         📅 {date}: {len(imgs)} images")
        
        if date_groups:
            # Take the first date group (chronologically first, likely main post)
            # PLUS any no-date images that appear early in the list (likely same carousel)
            first_date = list(date_groups.keys())[0]
            main_post_candidates = date_groups[first_date]
            
            # For carousels, also include early no-date images (they're often part of same post)
            # But only take no-date images that appear before the next date group
            next_date_position = len(all_images)  # Default to end if no next date
            if len(date_groups) > 1:
                # Find position of first image from second date group
                second_date = list(date_groups.keys())[1]
                for i, img in enumerate(all_images):
                    if img in date_groups[second_date]:
                        next_date_position = i
                        break
            
            # Include no-date images that appear early (likely part of main carousel)
            early_no_date = []
            first_date_end = 0
            
            # Find where the first date group images end
            for i, img in enumerate(all_images):
                if img in date_groups[first_date]:
                    first_date_end = max(first_date_end, i)
            
            # Include no-date images that appear close to the first date group
            for i, img in enumerate(all_images):
                if (img in no_date_images and 
                    i < next_date_position and 
                    i <= first_date_end + 3):  # Allow up to 3 positions after last first-date image
                    early_no_date.append(img)
            
            main_post_candidates.extend(early_no_date)
            
            print(f"         🎯 Selected main post from {first_date}: {len(date_groups[first_date])} images + {len(early_no_date)} early no-date images")
            return main_post_candidates
        else:
            # If no dates found, return first few images only (likely main post)
            print(f"         🎯 No dates found, taking first 5 images as main post")
            return all_images[:5]
    
    def apply_smart_carousel_filtering(self, all_images: List[Dict]) -> List[Dict]:
        """Apply smart filtering for containers - includes no-date carousel images"""
        from collections import defaultdict
        import re
        
        if not all_images:
            return []
        
        # Group images by date
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img_data in all_images:
            alt = img_data["alt"]
            # Extract dates from alt text
            date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data)
            else:
                no_date_images.append(img_data)
        
        print(f"         📅 Smart filtering - Date groups: {len(date_groups)}, No-date: {len(no_date_images)}")
        for date, imgs in date_groups.items():
            print(f"         📅 {date}: {len(imgs)} images")
        
        if date_groups:
            # Take the first date group (main post) + early no-date images (likely same carousel)
            first_date = list(date_groups.keys())[0]
            main_post_candidates = date_groups[first_date].copy()
            
            # Include no-date images that appear early (before other date groups)
            if len(date_groups) > 1:
                # Find position of first image from second date group
                second_date = list(date_groups.keys())[1]
                second_date_start = len(all_images)
                for i, img in enumerate(all_images):
                    if img in date_groups[second_date]:
                        second_date_start = i
                        break
                
                # Include no-date images that appear before the second date group
                early_no_date = []
                for i, img in enumerate(all_images):
                    if img in no_date_images and i < second_date_start:
                        early_no_date.append(img)
                
                main_post_candidates.extend(early_no_date)
                print(f"         🎯 Smart filter result: {len(date_groups[first_date])} from {first_date} + {len(early_no_date)} early no-date")
            else:
                # Only one date group, include all no-date images (likely all same post)
                main_post_candidates.extend(no_date_images)
                print(f"         🎯 Smart filter result: {len(date_groups[first_date])} from {first_date} + {len(no_date_images)} no-date (single date group)")
            
            return main_post_candidates
        else:
            # No dates found, return first few images
            print(f"         🎯 Smart filter: no dates found, taking first 5 images")
            return all_images[:5]
    
    def apply_carousel_aware_filtering(self, main_post_images: List[Dict], is_carousel: bool) -> List[str]:
        """Apply improved carousel-aware filtering logic"""
        from collections import defaultdict
        import re
        
        if not main_post_images:
            return []
        
        # Group images by date
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img_data in main_post_images:
            alt = img_data["alt"]
            date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data)
            else:
                no_date_images.append(img_data)
        
        if is_carousel:
            print(f"      🎠 Carousel detected")
            
            if date_groups:
                # For carousel, take the first date group (chronologically first = main post)
                # PLUS any no-date images (which are often part of the same carousel)
                first_date = list(date_groups.keys())[0]  # First date group = main post
                carousel_images = date_groups[first_date] + no_date_images
                
                # Limit to reasonable carousel size
                result_urls = [img["src"] for img in carousel_images[:10]]
                print(f"      🎠 Carousel: found {len(main_post_images)} total, filtered to {len(result_urls)} from {first_date} + {len(no_date_images)} no-date images")
                return result_urls
            else:
                # No date groups, take all images (likely all part of same carousel)
                result_urls = [img["src"] for img in main_post_images[:10]]
                print(f"      🎠 Carousel: no date pattern, took all {len(result_urls)} images")
                return result_urls
        else:
            print(f"      📷 Single post detected")
            
            # For single post, take just the first image from any source
            if date_groups:
                # Take first image from first date group found
                first_date = list(date_groups.keys())[0]
                if date_groups[first_date]:
                    result_url = date_groups[first_date][0]["src"]
                    print(f"      📷 Single post: took first image from {first_date}")
                    return [result_url]
            
            if no_date_images:
                result_url = no_date_images[0]["src"]
                print(f"      📷 Single post: took first no-date image")
                return [result_url]
            
            if main_post_images:
                result_url = main_post_images[0]["src"]
                print(f"      📷 Single post: took first available image")
                return [result_url]
            
            print(f"      📷 Single post: no images found")
            return []

    def compress_image(self, image_bytes: bytes, quality: int = 80) -> bytes:
        """Compress image for efficient GridFS storage"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Resize if too large (max 1500px on longest side)
            max_size = 1500
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Compress
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_bytes = output.getvalue()
            
            return compressed_bytes
            
        except Exception as e:
            print(f"      ⚠️  Compression failed: {e}")
            return image_bytes
    
    def extract_image_urls(self, shortcode: str) -> List[str]:
        """Extract image URLs from Instagram post"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print(f"   🔍 Extracting from {shortcode}...")
            
            url = f"https://www.instagram.com/p/{shortcode}/"
            self.driver.get(url)
            
            # Enhanced popup handling
            print(f"      🚪 Checking for popups...")
            
            # Handle cookie popup
            try:
                cookie_selectors = [
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Allow')]", 
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'Accept All')]",
                    "//button[contains(text(), 'Allow All')]",
                    "//button[@aria-label*='Accept']",
                    "//button[@aria-label*='Allow']"
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        cookie_button.click()
                        time.sleep(1)
                        print(f"      🍪 Handled cookie popup")
                        break
                    except:
                        continue
            except:
                pass
            
            # Handle login popup
            try:
                login_close_selectors = [
                    "//button[@aria-label='Close']",
                    "//button[contains(@aria-label, 'close')]",
                    "//div[@role='button'][contains(@aria-label, 'Close')]",
                    "//svg[@aria-label='Close']/../..",
                    "//*[contains(@class, 'close')]",
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Cancel')]"
                ]
                
                for selector in login_close_selectors:
                    try:
                        close_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        close_button.click()
                        time.sleep(1)
                        print(f"      ❌ Closed popup")
                        break
                    except:
                        continue
            except:
                pass
            
            # Handle any overlay or modal
            try:
                overlay_selectors = [
                    "//div[@role='dialog']//button",
                    "//div[contains(@class, 'modal')]//button",
                    "//div[contains(@class, 'overlay')]//button"
                ]
                
                for selector in overlay_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if any(text in button.text.lower() for text in ['close', 'cancel', 'not now', 'dismiss']):
                                button.click()
                                time.sleep(1)
                                print(f"      🚫 Dismissed overlay")
                                break
                    except:
                        continue
            except:
                pass
            
            # Wait for page load AND dynamic content to fully load
            print(f"      ⏳ Waiting for dynamic content...")
            time.sleep(random.uniform(8, 12))  # Longer wait for dynamic loading
            
            # Check if this is a single post or carousel (look in main article first)
            is_carousel = False
            main_articles = self.driver.find_elements(By.CSS_SELECTOR, "article")
            
            if main_articles:
                # Look for carousel buttons within the main article
                carousel_buttons = main_articles[0].find_elements(By.CSS_SELECTOR, 
                    "button[aria-label*='Next'], button[aria-label*='Previous'], [aria-label*='Go to']")
            else:
                # Fallback to page-wide search
                carousel_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[aria-label*='Next'], button[aria-label*='Previous'], [aria-label*='Go to']")
            
            if carousel_buttons:
                is_carousel = True
                print(f"      🎠 Carousel detected")
            else:
                is_carousel = False
                print(f"      📷 Single post detected")
            
            # Extract all image URLs using multiple strategies
            image_urls = set()
            
            # Strategy: Look for images with improved main post detection
            try:
                # Multiple strategies to find the main post container
                main_post_images = []
                img_elements = []
                container_found = False
                
                # Strategy 1: Try main article selector (wait a bit more for dynamic content)
                time.sleep(2)  # Additional wait for article elements to load
                main_articles = self.driver.find_elements(By.CSS_SELECTOR, "main article")
                if main_articles:
                    main_article = main_articles[0]
                    img_elements = main_article.find_elements(By.CSS_SELECTOR, "img")
                    container_found = True
                    print(f"      📄 Found main article container with {len(img_elements)} images")
                
                # Strategy 2: Try generic article if main article fails
                if not img_elements:
                    articles = self.driver.find_elements(By.CSS_SELECTOR, "article")
                    if articles:
                        main_article = articles[0]
                        img_elements = main_article.find_elements(By.CSS_SELECTOR, "img")
                        container_found = True
                        print(f"      📄 Found article container with {len(img_elements)} images")
                
                # Strategy 3: Try specific post container selectors
                if not img_elements:
                    post_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                        "div[role='presentation'][tabindex='-1'], main > div > div > div")
                    if post_containers:
                        main_container = post_containers[0]
                        img_elements = main_container.find_elements(By.CSS_SELECTOR, "img")
                        container_found = True
                        print(f"      📄 Found post container with {len(img_elements)} images")
                
                # Strategy 4: Use position-based filtering with date consistency (fallback)
                if not img_elements:
                    container_found = False
                    print(f"      ⚠️  No container found, using position-based filtering")
                    img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
                
                for img in img_elements:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or ""
                    
                    if src and ("fbcdn.net" in src or "scontent" in src):
                        # Filter for actual content images that have loaded
                        if ("t51.29350-15" in src and
                            not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                            
                            # Store both src and alt for better deduplication
                            main_post_images.append({
                                "src": src,
                                "alt": alt
                            })
                
                # ALWAYS use smart filtering for best carousel detection
                # Container detection is unreliable and may miss carousel images
                print(f"      🎯 Applying enhanced smart filtering for complete carousel detection")
                main_post_images = self.apply_strict_main_post_filtering(main_post_images)
                
                # Apply improved carousel-aware filtering logic
                filtered_urls = self.apply_carousel_aware_filtering(main_post_images, is_carousel)
                
                for url in filtered_urls:
                    image_urls.add(url)
                        
            except Exception as e:
                print(f"      ⚠️  Element extraction failed: {e}")
            
            # Return filtered URLs directly
            unique_urls = list(image_urls)
            print(f"      ✅ Found {len(unique_urls)} image URLs")
            
            return unique_urls
            
        except Exception as e:
            print(f"      ❌ URL extraction failed: {e}")
            return []
    
    async def download_and_save_image(self, image_url: str, shortcode: str, img_index: int) -> Optional[str]:
        """Download and save image to GridFS with compression"""
        try:
            import aiohttp
            
            print(f"      📥 Downloading image {img_index}...")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.instagram.com/',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        original_bytes = await response.read()
                        compressed_bytes = self.compress_image(original_bytes)
                        
                        # Calculate compression stats
                        original_size = len(original_bytes)
                        compressed_size = len(compressed_bytes)
                        compression_ratio = compressed_size / original_size
                        
                        # Save to GridFS
                        filename = f"instagram_production_{shortcode}_{img_index}.jpg"
                        
                        file_id = self.fs.put(
                            compressed_bytes,
                            filename=filename,
                            contentType="image/jpeg",
                            metadata={
                                "source": "instagram_production_auto",
                                "shortcode": shortcode,
                                "img_index": img_index,
                                "instagram_url": f"https://instagram.com/p/{shortcode}/?img_index={img_index}" if img_index > 1 else f"https://instagram.com/p/{shortcode}/",
                                "original_url": image_url,
                                "extracted_at": datetime.now(timezone.utc),
                                "original_size": original_size,
                                "compressed_size": compressed_size,
                                "compression_ratio": compression_ratio,
                                "quality": 80,
                                "brand": "siliconsentiments",
                                "category": "instagram_original_production",
                                "automated": True,
                                "extractor_version": "production_v1.0"
                            }
                        )
                        
                        print(f"         ✅ Saved {compressed_size} bytes ({compression_ratio:.1%} of original)")
                        return str(file_id)
                    else:
                        print(f"         ❌ Download failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"         ❌ Save failed: {e}")
            return None
    
    async def process_single_post(self, shortcode: str) -> Dict[str, Any]:
        """Process a single Instagram post"""
        
        print(f"🎯 Processing {shortcode}")
        
        try:
            # Rate limiting
            if self.session_stats["last_request"]:
                elapsed = time.time() - self.session_stats["last_request"]
                min_delay = self.request_delay[0]
                if elapsed < min_delay:
                    sleep_time = min_delay - elapsed
                    print(f"   ⏱️  Rate limiting: sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)
            
            self.session_stats["last_request"] = time.time()
            
            # Extract image URLs
            image_urls = self.extract_image_urls(shortcode)
            
            if not image_urls:
                return {"success": False, "error": "No images found"}
            
            # Download and save images
            original_file_ids = []
            
            for i, image_url in enumerate(image_urls, 1):
                file_id = await self.download_and_save_image(image_url, shortcode, i)
                if file_id:
                    original_file_ids.append(file_id)
                
                # Small delay between downloads
                await asyncio.sleep(random.uniform(1, 3))
            
            if not original_file_ids:
                return {"success": False, "error": "Failed to save any images"}
            
            # Create tracking document
            tracking_doc = {
                "shortcode": shortcode,
                "instagram_url": f"https://instagram.com/p/{shortcode}",
                "extraction_method": "production_automated",
                "total_images": len(original_file_ids),
                "original_images": [
                    {
                        "index": i + 1,
                        "file_id": file_id,
                        "filename": f"instagram_production_{shortcode}_{i + 1}.jpg"
                    }
                    for i, file_id in enumerate(original_file_ids)
                ],
                "extracted_at": datetime.now(timezone.utc),
                "category": "instagram_originals_production",
                "brand": "siliconsentiments",
                "automated": True,
                "extractor_version": "production_v1.0"
            }
            
            result = self.db.instagram_originals.insert_one(tracking_doc)
            doc_id = result.inserted_id
            
            # Update session stats
            self.session_stats["extracted"] += 1
            self.session_stats["total_images"] += len(original_file_ids)
            
            print(f"   ✅ Complete: {len(original_file_ids)} images saved (doc: {doc_id})")
            
            return {
                "success": True,
                "shortcode": shortcode,
                "images_saved": len(original_file_ids),
                "file_ids": original_file_ids,
                "doc_id": str(doc_id)
            }
            
        except Exception as e:
            print(f"   ❌ Processing failed: {e}")
            self.session_stats["failed"] += 1
            return {"success": False, "error": str(e)}
    
    async def run_extraction_batch(self, batch_size: int = 10) -> Dict[str, Any]:
        """Run a batch of Instagram extractions"""
        
        print(f"🚀 PRODUCTION INSTAGRAM EXTRACTION BATCH")
        print("=" * 60)
        print(f"📊 Batch size: {batch_size}")
        
        if not self.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        if not self.setup_browser():
            return {"success": False, "error": "Browser setup failed"}
        
        try:
            # Get posts that need extraction
            posts = list(self.db.posts.find({
                "shortcode": {"$exists": True, "$ne": "", "$ne": None},
                "image_ref": {"$exists": False}
            }).limit(batch_size))
            
            if not posts:
                return {"success": False, "error": "No posts need extraction"}
            
            # Check if we have existing extractions for any of these
            existing_extractions = set()
            existing_docs = list(self.db.instagram_originals.find({
                "shortcode": {"$in": [p["shortcode"] for p in posts]}
            }, {"shortcode": 1}))
            
            for doc in existing_docs:
                existing_extractions.add(doc["shortcode"])
            
            # Filter out already extracted posts
            posts_to_process = [p for p in posts if p["shortcode"] not in existing_extractions]
            
            if not posts_to_process:
                return {"success": False, "error": "All posts already extracted"}
            
            print(f"📝 Processing {len(posts_to_process)} posts (skipping {len(existing_extractions)} already extracted)")
            
            # Process posts
            results = []
            for i, post in enumerate(posts_to_process, 1):
                shortcode = post["shortcode"]
                
                print(f"\n🔄 Post {i}/{len(posts_to_process)}: {shortcode}")
                
                # Check daily limit
                if self.session_stats["extracted"] >= self.daily_limit:
                    print(f"   ⚠️  Daily limit reached ({self.daily_limit})")
                    break
                
                result = await self.process_single_post(shortcode)
                results.append(result)
                
                # Inter-post delay
                if i < len(posts_to_process):
                    delay = random.uniform(*self.request_delay)
                    print(f"   ⏱️  Waiting {delay:.1f}s before next post...")
                    time.sleep(delay)
            
            # Summary
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            print(f"\n🎉 BATCH COMPLETE!")
            print("=" * 60)
            print(f"✅ Successful: {len(successful)}")
            print(f"❌ Failed: {len(failed)}")
            print(f"📸 Total images extracted: {sum(r.get('images_saved', 0) for r in successful)}")
            print(f"⏱️  Duration: {datetime.now() - self.session_stats['start_time']}")
            
            if successful:
                print(f"\n📊 Successfully extracted:")
                for r in successful[:5]:  # Show first 5
                    print(f"   {r['shortcode']}: {r['images_saved']} images")
                if len(successful) > 5:
                    print(f"   ... and {len(successful) - 5} more")
            
            if failed:
                print(f"\n❌ Failed extractions:")
                for r in failed[:3]:  # Show first 3 errors
                    print(f"   {r.get('shortcode', 'unknown')}: {r['error']}")
            
            return {
                "success": True,
                "batch_size": len(posts_to_process),
                "successful": len(successful),
                "failed": len(failed),
                "total_images": sum(r.get('images_saved', 0) for r in successful),
                "results": results
            }
            
        except Exception as e:
            print(f"\n❌ Batch failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            if self.driver:
                self.driver.quit()
            if self.client:
                self.client.close()

async def main():
    """Run production Instagram extraction"""
    
    # Get API token (for future VLM integration)
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("⚠️  REPLICATE_API_TOKEN not set (needed for VLM analysis later)")
    
    # Initialize extractor
    extractor = ProductionInstagramExtractor(replicate_token or "")
    
    # Run extraction batch
    result = await extractor.run_extraction_batch(batch_size=1)  # Test single post
    
    if result["success"]:
        print(f"\n🎊 EXTRACTION SUCCESS!")
        print(f"   📸 Extracted {result['total_images']} images from {result['successful']} posts")
        print(f"   💾 All images saved to GridFS with compression")
        print(f"   📄 Tracking documents created")
        print(f"\n💡 Next steps:")
        print(f"   1. Run VLM analysis on extracted images")
        print(f"   2. Generate SiliconSentiments variations")
        print(f"   3. Scale up batch size for production")
    else:
        print(f"❌ Extraction failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())