#!/usr/bin/env python3
"""
Automated Instagram Image Extractor

Uses browser automation with anti-detection to:
1. Extract images from Instagram posts (including carousels)
2. Save originals to GridFS with compression
3. Handle rate limiting and anti-bot measures
4. Create complete pipeline automation
"""

import os
import asyncio
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import json
import base64
from PIL import Image
import io

class AutomatedInstagramExtractor:
    """Automated Instagram image extraction with anti-detection"""
    
    def __init__(self, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
        self.driver = None
        
        # Anti-detection settings
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Rate limiting
        self.request_delay = (2, 5)  # Random delay between requests
        self.batch_delay = (30, 60)  # Delay between batches
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with anti-detection"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print("🤖 Setting up automated browser...")
            
            options = Options()
            
            # Anti-detection options
            options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Performance options
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            
            # Headless mode (comment out for debugging)
            options.add_argument("--headless")
            
            # Create driver
            self.driver = webdriver.Chrome(options=options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("   ✅ Browser initialized")
            return True
            
        except Exception as e:
            print(f"   ❌ Browser setup failed: {e}")
            print("   💡 Install ChromeDriver: brew install chromedriver")
            return False
    
    def compress_image(self, image_bytes: bytes, quality: int = 85) -> bytes:
        """Compress image for GridFS storage"""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Compress
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_bytes = output.getvalue()
            
            compression_ratio = len(compressed_bytes) / len(image_bytes)
            print(f"      📦 Compressed: {len(image_bytes)} → {len(compressed_bytes)} bytes ({compression_ratio:.2%})")
            
            return compressed_bytes
            
        except Exception as e:
            print(f"      ⚠️  Compression failed: {e}, using original")
            return image_bytes
    
    def extract_images_from_page(self, shortcode: str) -> List[Dict[str, Any]]:
        """Extract all images from Instagram post page"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print(f"🔍 Extracting images from {shortcode}...")
            
            url = f"https://www.instagram.com/p/{shortcode}/"
            self.driver.get(url)
            
            # Wait for page load
            time.sleep(random.uniform(3, 6))
            
            # Try multiple image extraction strategies
            images = []
            
            # Strategy 1: Look for main image elements
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "article img")
                for i, img in enumerate(img_elements):
                    src = img.get_attribute("src")
                    if src and "scontent" in src and any(ext in src for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        images.append({
                            "index": i + 1,
                            "url": src,
                            "method": "main_img_elements",
                            "element_info": {
                                "alt": img.get_attribute("alt"),
                                "width": img.get_attribute("width"),
                                "height": img.get_attribute("height")
                            }
                        })
            except Exception as e:
                print(f"      ⚠️  Strategy 1 failed: {e}")
            
            # Strategy 2: Check for carousel navigation
            try:
                # Look for carousel indicators
                carousel_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Next']")
                if carousel_buttons:
                    print(f"      🎠 Detected carousel, navigating through images...")
                    
                    # Click through carousel
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        try:
                            # Get current image
                            current_img = self.driver.find_element(By.CSS_SELECTOR, "article img")
                            src = current_img.get_attribute("src")
                            
                            if src and "scontent" in src:
                                # Check if we already have this image
                                if not any(img["url"] == src for img in images):
                                    images.append({
                                        "index": len(images) + 1,
                                        "url": src,
                                        "method": "carousel_navigation",
                                        "carousel_position": attempt + 1
                                    })
                            
                            # Try to click next
                            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
                            if next_button.is_enabled():
                                next_button.click()
                                time.sleep(random.uniform(1, 2))
                            else:
                                break
                                
                        except Exception as e:
                            print(f"         ⚠️  Carousel position {attempt + 1} failed: {e}")
                            break
                            
            except Exception as e:
                print(f"      ⚠️  Strategy 2 failed: {e}")
            
            # Strategy 3: Extract from page source
            try:
                page_source = self.driver.page_source
                import re
                
                patterns = [
                    r'"display_url":"([^"]+)"',
                    r'"src":"([^"]+scontent[^"]+\.jpg[^"]*)"',
                    r'src="([^"]+scontent[^"]+\.jpg[^"]*)"'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source)
                    for match in matches:
                        clean_url = match.replace('\\u0026', '&').replace('\\/', '/')
                        if "scontent" in clean_url and not any(img["url"] == clean_url for img in images):
                            images.append({
                                "index": len(images) + 1,
                                "url": clean_url,
                                "method": "page_source_regex"
                            })
                            
            except Exception as e:
                print(f"      ⚠️  Strategy 3 failed: {e}")
            
            # Remove duplicates and sort
            unique_images = []
            seen_urls = set()
            
            for img in images:
                if img["url"] not in seen_urls:
                    seen_urls.add(img["url"])
                    unique_images.append(img)
            
            print(f"      ✅ Found {len(unique_images)} unique images")
            return unique_images
            
        except Exception as e:
            print(f"      ❌ Image extraction failed: {e}")
            return []
    
    async def download_and_save_image(self, image_info: Dict[str, Any], shortcode: str) -> Optional[str]:
        """Download image and save to GridFS with compression"""
        try:
            import aiohttp
            
            image_url = image_info["url"]
            img_index = image_info["index"]
            
            print(f"      📥 Downloading image {img_index}...")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.instagram.com/',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        original_bytes = await response.read()
                        
                        # Compress image
                        compressed_bytes = self.compress_image(original_bytes)
                        
                        # Save to GridFS
                        filename = f"instagram_auto_{shortcode}_{img_index}.jpg"
                        
                        file_id = self.fs.put(
                            compressed_bytes,
                            filename=filename,
                            contentType="image/jpeg",
                            metadata={
                                "source": "instagram_automated",
                                "shortcode": shortcode,
                                "img_index": img_index,
                                "instagram_url": f"https://instagram.com/p/{shortcode}/?img_index={img_index}" if img_index > 1 else f"https://instagram.com/p/{shortcode}/",
                                "original_url": image_url,
                                "downloaded_at": datetime.now(timezone.utc),
                                "original_size": len(original_bytes),
                                "compressed_size": len(compressed_bytes),
                                "compression_ratio": len(compressed_bytes) / len(original_bytes),
                                "extraction_method": image_info.get("method", "unknown"),
                                "brand": "siliconsentiments",
                                "category": "instagram_original_auto",
                                "automated": True
                            }
                        )
                        
                        print(f"         ✅ Saved to GridFS: {file_id}")
                        return str(file_id)
                    else:
                        print(f"         ❌ Download failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"         ❌ Download/save failed: {e}")
            return None
    
    async def extract_post_automatically(self, shortcode: str) -> Dict[str, Any]:
        """Automatically extract all images from an Instagram post"""
        
        print(f"🤖 AUTOMATED EXTRACTION: {shortcode}")
        print("-" * 50)
        
        try:
            # Setup browser if needed
            if not self.driver:
                if not self.setup_selenium_driver():
                    return {"success": False, "error": "Browser setup failed"}
            
            # Extract images from page
            images = self.extract_images_from_page(shortcode)
            
            if not images:
                return {"success": False, "error": "No images found"}
            
            # Download and save all images
            print(f"📥 Downloading {len(images)} images...")
            original_file_ids = []
            
            for image_info in images:
                file_id = await self.download_and_save_image(image_info, shortcode)
                if file_id:
                    original_file_ids.append(file_id)
                
                # Rate limiting
                await asyncio.sleep(random.uniform(*self.request_delay))
            
            if not original_file_ids:
                return {"success": False, "error": "Failed to save any images"}
            
            # Create tracking document
            original_doc = {
                "shortcode": shortcode,
                "instagram_url": f"https://instagram.com/p/{shortcode}",
                "extraction_method": "automated_selenium",
                "total_images": len(original_file_ids),
                "original_images": [
                    {
                        "index": i + 1,
                        "file_id": file_id,
                        "filename": f"instagram_auto_{shortcode}_{i + 1}.jpg"
                    }
                    for i, file_id in enumerate(original_file_ids)
                ],
                "extracted_at": datetime.now(timezone.utc),
                "category": "instagram_originals_auto",
                "brand": "siliconsentiments",
                "automated": True
            }
            
            result = self.db.instagram_originals.insert_one(original_doc)
            doc_id = result.inserted_id
            
            print(f"✅ Extraction complete: {len(original_file_ids)} images saved")
            print(f"📄 Tracking document: {doc_id}")
            
            return {
                "success": True,
                "shortcode": shortcode,
                "images_found": len(images),
                "images_saved": len(original_file_ids),
                "original_file_ids": original_file_ids,
                "doc_id": str(doc_id)
            }
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup(self):
        """Cleanup browser and connections"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        if self.client:
            self.client.close()

class InstagramAnalyzer:
    """Analyze current database state for Instagram images"""
    
    def __init__(self, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current state of Instagram images in database"""
        
        print("📊 ANALYZING CURRENT INSTAGRAM IMAGE STATE")
        print("=" * 60)
        
        try:
            # Basic post statistics
            total_posts = self.db.posts.count_documents({})
            posts_with_images = self.db.posts.count_documents({"image_ref": {"$exists": True}})
            posts_without_images = total_posts - posts_with_images
            posts_with_shortcodes = self.db.posts.count_documents({"shortcode": {"$exists": True, "$ne": "", "$ne": None}})
            
            print(f"📝 POSTS OVERVIEW:")
            print(f"   Total posts: {total_posts:,}")
            print(f"   Posts with images: {posts_with_images:,}")
            print(f"   Posts without images: {posts_without_images:,}")
            print(f"   Posts with shortcodes: {posts_with_shortcodes:,}")
            
            # Original images analysis
            original_images = self.db.instagram_originals.count_documents({})
            automated_originals = self.db.instagram_originals.count_documents({"automated": True})
            
            print(f"\n📸 ORIGINAL IMAGES:")
            print(f"   Original image collections: {original_images}")
            print(f"   Automated extractions: {automated_originals}")
            
            # GridFS analysis
            gridfs_files = self.db.fs.files.count_documents({})
            instagram_originals = self.db.fs.files.count_documents({"metadata.category": {"$regex": "instagram_original"}})
            
            print(f"\n💾 GRIDFS STORAGE:")
            print(f"   Total files: {gridfs_files:,}")
            print(f"   Instagram originals: {instagram_originals}")
            
            # URL analysis in existing generations
            posts_with_urls = 0
            posts_accessible_urls = 0
            
            sample_posts = list(self.db.posts.find({"image_ref": {"$exists": True}}).limit(100))
            
            for post in sample_posts:
                try:
                    image_doc = self.db.post_images.find_one({"_id": post["image_ref"]})
                    if image_doc and "images" in image_doc:
                        for img in image_doc["images"]:
                            if "midjourney_generations" in img:
                                for gen in img["midjourney_generations"]:
                                    if gen.get("image_url"):
                                        posts_with_urls += 1
                                        # Could test URL accessibility here
                                        if gen["image_url"].startswith("http"):
                                            posts_accessible_urls += 1
                                        break
                except:
                    continue
            
            print(f"\n🔗 URL ANALYSIS (sample of 100 posts):")
            print(f"   Posts with image URLs: {posts_with_urls}")
            print(f"   Potentially accessible URLs: {posts_accessible_urls}")
            
            # Priority posts for extraction
            priority_posts = list(self.db.posts.find({
                "shortcode": {"$exists": True, "$ne": "", "$ne": None},
                "image_ref": {"$exists": False}
            }).limit(10))
            
            print(f"\n🎯 PRIORITY POSTS FOR EXTRACTION:")
            print(f"   Posts without images but with shortcodes: {posts_without_images}")
            print(f"   Sample shortcodes:")
            for post in priority_posts[:5]:
                shortcode = post.get("shortcode", "unknown")
                print(f"      {shortcode} - https://instagram.com/p/{shortcode}")
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            
            if posts_without_images > 1000:
                print(f"   🔥 HIGH PRIORITY: {posts_without_images:,} posts need images")
                print(f"   📈 Automated extraction could process ~50-100 posts/day")
                print(f"   ⏱️  Estimated time: {posts_without_images // 75} days at 75 posts/day")
            
            if instagram_originals < 100:
                print(f"   📸 Start building original image collection with automation")
                print(f"   💾 GridFS compression will save storage space")
            
            print(f"   🤖 Automated extraction recommended for scale")
            print(f"   ⚡ Can run VLM analysis on extracted originals")
            
            return {
                "total_posts": total_posts,
                "posts_with_images": posts_with_images,
                "posts_without_images": posts_without_images,
                "posts_with_shortcodes": posts_with_shortcodes,
                "original_images": original_images,
                "priority_shortcodes": [p.get("shortcode") for p in priority_posts[:10]],
                "estimated_extraction_time_days": posts_without_images // 75,
                "automation_recommended": posts_without_images > 100
            }
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {"error": str(e)}
        
        finally:
            if self.client:
                self.client.close()

async def demo_automated_extraction():
    """Demo automated Instagram extraction"""
    
    print("🤖 AUTOMATED INSTAGRAM EXTRACTION DEMO")
    print("=" * 60)
    
    # First analyze current state
    analyzer = InstagramAnalyzer()
    if analyzer.connect():
        analysis = analyzer.analyze_current_state()
        
        if analysis.get("automation_recommended"):
            print(f"\n🚀 AUTOMATION RECOMMENDED!")
            print(f"   Posts to process: {analysis['posts_without_images']:,}")
            print(f"   Sample shortcodes: {analysis['priority_shortcodes'][:3]}")
            
            # Demo extraction (uncomment to run)
            """
            extractor = AutomatedInstagramExtractor()
            if extractor.connect_to_mongodb():
                
                # Test with first priority shortcode
                test_shortcode = analysis['priority_shortcodes'][0]
                result = await extractor.extract_post_automatically(test_shortcode)
                
                if result["success"]:
                    print(f"✅ Successfully extracted {result['images_saved']} images!")
                    print(f"📄 Document ID: {result['doc_id']}")
                else:
                    print(f"❌ Extraction failed: {result['error']}")
                
                extractor.cleanup()
            """
            
            print(f"\n💡 To run automated extraction:")
            print(f"   1. Install: pip install selenium pillow")
            print(f"   2. Install ChromeDriver: brew install chromedriver")
            print(f"   3. Uncomment the demo code above")
            print(f"   4. Run the extraction!")
        else:
            print(f"\n📊 Current state looks good!")

if __name__ == "__main__":
    asyncio.run(demo_automated_extraction())