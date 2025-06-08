#!/usr/bin/env python3
"""
Advanced Instagram Image Fetcher

Handles carousel posts and saves original images to GridFS:
1. Detects carousel posts with multiple images
2. Fetches all images from img_index=1 to 10
3. Saves originals to GridFS with metadata
4. Uses multiple scraping strategies
5. Creates proper comparison structure
"""

import os
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

class AdvancedInstagramFetcher:
    """Advanced Instagram fetcher for carousel posts with GridFS storage"""
    
    def __init__(self, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
        
        # Local comparison directory
        self.comparison_dir = "instagram_carousel_comparison"
        os.makedirs(self.comparison_dir, exist_ok=True)
    
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB for original image storage")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def detect_carousel_type(self, shortcode: str) -> Dict[str, Any]:
        """Detect if post is carousel and how many images it has"""
        try:
            print(f"🔍 Detecting carousel structure for {shortcode}")
            
            base_url = f"https://www.instagram.com/p/{shortcode}/"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                # Try base URL first
                async with session.get(base_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Look for carousel indicators
                        carousel_patterns = [
                            r'"edge_sidecar_to_children".*?"count":(\d+)',
                            r'"carousel_media_count":(\d+)',
                            r'img_index=(\d+)',
                            r'"media_count":(\d+)'
                        ]
                        
                        max_images = 1
                        is_carousel = False
                        
                        for pattern in carousel_patterns:
                            matches = re.findall(pattern, html)
                            if matches:
                                count = max(int(m) for m in matches)
                                if count > max_images:
                                    max_images = count
                                    is_carousel = True
                        
                        # Test img_index approach
                        if not is_carousel:
                            print("   🔍 Testing for carousel with img_index...")
                            for i in range(2, 11):  # Test up to 10 images
                                test_url = f"{base_url}?img_index={i}"
                                async with session.get(test_url, headers=headers) as test_response:
                                    if test_response.status == 200:
                                        max_images = i
                                        is_carousel = True
                                    else:
                                        break
                        
                        print(f"   📊 Result: {'Carousel' if is_carousel else 'Single'} post with {max_images} image(s)")
                        
                        return {
                            "is_carousel": is_carousel,
                            "image_count": max_images,
                            "shortcode": shortcode,
                            "base_url": base_url
                        }
                    else:
                        print(f"   ❌ Failed to access {shortcode}: HTTP {response.status}")
                        return {"is_carousel": False, "image_count": 1, "shortcode": shortcode}
                        
        except Exception as e:
            print(f"   ❌ Carousel detection failed: {e}")
            return {"is_carousel": False, "image_count": 1, "shortcode": shortcode}
    
    async def fetch_carousel_images(self, shortcode: str, image_count: int) -> List[Dict[str, Any]]:
        """Fetch all images from a carousel post"""
        
        print(f"📸 Fetching {image_count} images from carousel {shortcode}")
        
        images = []
        base_url = f"https://www.instagram.com/p/{shortcode}/"
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.instagram.com/',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            for img_index in range(1, image_count + 1):
                try:
                    if img_index == 1:
                        url = base_url
                    else:
                        url = f"{base_url}?img_index={img_index}"
                    
                    print(f"   📥 Fetching image {img_index}/{image_count}...")
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Multiple image URL extraction patterns
                            image_url = await self.extract_image_from_html(html, img_index)
                            
                            if image_url:
                                print(f"      ✅ Found image URL for index {img_index}")
                                images.append({
                                    "index": img_index,
                                    "url": image_url,
                                    "instagram_url": url,
                                    "extracted_at": datetime.now(timezone.utc)
                                })
                            else:
                                print(f"      ❌ No image URL found for index {img_index}")
                        else:
                            print(f"      ❌ Failed to fetch index {img_index}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"      ❌ Error fetching image {img_index}: {e}")
                
                # Small delay to be respectful
                await asyncio.sleep(0.5)
        
        print(f"   📊 Successfully found {len(images)} image URLs")
        return images
    
    async def extract_image_from_html(self, html: str, img_index: int) -> Optional[str]:
        """Extract image URL from HTML using multiple patterns"""
        try:
            # Enhanced patterns for different Instagram layouts
            patterns = [
                # High resolution patterns
                r'"display_url":"([^"]+)"',
                r'"src":"([^"]+\.jpg[^"]*)"',
                r'"url":"([^"]+\.jpg[^"]*)"',
                
                # Open Graph patterns
                r'property="og:image"[^>]*content="([^"]+)"',
                r'content="([^"]+\.jpg[^"]*)"[^>]*property="og:image"',
                
                # Script JSON patterns
                r'"display_resources":\[{"src":"([^"]+)"',
                r'"thumbnail_src":"([^"]+)"',
                r'"config_width":\d+,"config_height":\d+,"src":"([^"]+)"',
                
                # Direct image tags
                r'<img[^>]+src="([^"]+scontent[^"]+\.jpg[^"]*)"',
                r'data-src="([^"]+scontent[^"]+\.jpg[^"]*)"',
                
                # Video thumbnail fallback
                r'"video_url":"([^"]+)"',
                r'"thumbnail_url":"([^"]+)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    for match in matches:
                        # Clean up the URL
                        image_url = match.replace('\\u0026', '&').replace('\\/', '/').replace('\\', '')
                        
                        # Validate the URL
                        if self.is_valid_instagram_image_url(image_url):
                            return image_url
            
            return None
            
        except Exception as e:
            print(f"      ❌ HTML extraction error: {e}")
            return None
    
    def is_valid_instagram_image_url(self, url: str) -> bool:
        """Validate if URL looks like a real Instagram image"""
        try:
            # Must contain Instagram CDN patterns
            instagram_patterns = [
                'scontent',
                'cdninstagram',
                'fbcdn'
            ]
            
            # Must be an image format
            image_formats = ['.jpg', '.jpeg', '.png', '.webp']
            
            has_instagram_pattern = any(pattern in url.lower() for pattern in instagram_patterns)
            has_image_format = any(fmt in url.lower() for fmt in image_formats)
            
            # Must be HTTPS
            is_https = url.startswith('https://')
            
            # Reasonable length
            reasonable_length = 50 < len(url) < 500
            
            return has_instagram_pattern and has_image_format and is_https and reasonable_length
            
        except:
            return False
    
    async def download_and_save_original(self, image_data: Dict[str, Any], shortcode: str) -> Optional[str]:
        """Download original image and save to GridFS"""
        try:
            image_url = image_data["url"]
            img_index = image_data["index"]
            
            print(f"      💾 Downloading image {img_index} to GridFS...")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.instagram.com/',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        
                        # Save to GridFS
                        filename = f"instagram_original_{shortcode}_{img_index}.jpg"
                        
                        file_id = self.fs.put(
                            image_bytes,
                            filename=filename,
                            contentType="image/jpeg",
                            metadata={
                                "source": "instagram_original",
                                "shortcode": shortcode,
                                "img_index": img_index,
                                "instagram_url": image_data["instagram_url"],
                                "original_url": image_url,
                                "downloaded_at": datetime.now(timezone.utc),
                                "file_size": len(image_bytes),
                                "is_carousel": True,
                                "total_images": None,  # Will be updated later
                                "brand": "siliconsentiments",
                                "category": "instagram_original"
                            }
                        )
                        
                        # Also save locally for comparison
                        local_filename = f"{shortcode}_original_{img_index}.jpg"
                        local_path = os.path.join(self.comparison_dir, local_filename)
                        
                        with open(local_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        print(f"         ✅ Saved to GridFS: {file_id}")
                        print(f"         ✅ Saved locally: {local_filename}")
                        print(f"         📏 Size: {len(image_bytes)} bytes")
                        
                        return str(file_id)
                    else:
                        print(f"         ❌ Download failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"         ❌ Save failed: {e}")
            return None
    
    def create_original_images_document(self, shortcode: str, original_file_ids: List[str], carousel_info: Dict[str, Any]) -> Optional[str]:
        """Create a document to track original Instagram images"""
        try:
            print(f"📄 Creating original images document...")
            
            original_doc = {
                "shortcode": shortcode,
                "instagram_url": f"https://instagram.com/p/{shortcode}",
                "is_carousel": carousel_info["is_carousel"],
                "total_images": len(original_file_ids),
                "original_images": [
                    {
                        "index": i + 1,
                        "file_id": file_id,
                        "filename": f"instagram_original_{shortcode}_{i + 1}.jpg",
                        "instagram_url": f"https://instagram.com/p/{shortcode}/?img_index={i + 1}" if i > 0 else f"https://instagram.com/p/{shortcode}/"
                    }
                    for i, file_id in enumerate(original_file_ids)
                ],
                "created_at": datetime.now(timezone.utc),
                "fetched_at": datetime.now(timezone.utc),
                "category": "instagram_originals",
                "brand": "siliconsentiments",
                "status": "original_images_stored"
            }
            
            # Insert document
            result = self.db.instagram_originals.insert_one(original_doc)
            doc_id = result.inserted_id
            
            print(f"   ✅ Original images document created: {doc_id}")
            
            return str(doc_id)
            
        except Exception as e:
            print(f"   ❌ Original document creation failed: {e}")
            return None
    
    async def fetch_complete_instagram_post(self, shortcode: str) -> Dict[str, Any]:
        """Complete pipeline to fetch all images from an Instagram post"""
        
        print(f"🚀 FETCHING COMPLETE INSTAGRAM POST: {shortcode}")
        print("=" * 60)
        
        if not self.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # Step 1: Detect carousel structure
            print("1️⃣ DETECTING CAROUSEL STRUCTURE...")
            carousel_info = await self.detect_carousel_type(shortcode)
            
            # Step 2: Fetch all images
            print("\n2️⃣ FETCHING IMAGES...")
            images = await self.fetch_carousel_images(shortcode, carousel_info["image_count"])
            
            if not images:
                return {
                    "success": False, 
                    "error": "No images could be fetched",
                    "carousel_info": carousel_info
                }
            
            # Step 3: Download and save to GridFS
            print("\n3️⃣ DOWNLOADING AND SAVING TO GRIDFS...")
            original_file_ids = []
            
            for image_data in images:
                file_id = await self.download_and_save_original(image_data, shortcode)
                if file_id:
                    original_file_ids.append(file_id)
            
            if not original_file_ids:
                return {
                    "success": False,
                    "error": "Failed to save any images",
                    "images_found": len(images)
                }
            
            # Step 4: Create tracking document
            print("\n4️⃣ CREATING TRACKING DOCUMENT...")
            original_doc_id = self.create_original_images_document(shortcode, original_file_ids, carousel_info)
            
            print(f"\n🎉 INSTAGRAM FETCH COMPLETE!")
            print("=" * 60)
            print(f"✅ Successfully fetched Instagram post")
            print(f"📱 Shortcode: {shortcode}")
            print(f"🖼️  Type: {'Carousel' if carousel_info['is_carousel'] else 'Single'}")
            print(f"📊 Images found: {len(images)}")
            print(f"💾 Images saved: {len(original_file_ids)}")
            print(f"📄 Tracking document: {original_doc_id}")
            print(f"📂 Local comparison folder: {os.path.abspath(self.comparison_dir)}")
            
            return {
                "success": True,
                "shortcode": shortcode,
                "carousel_info": carousel_info,
                "images_found": len(images),
                "images_saved": len(original_file_ids),
                "original_file_ids": original_file_ids,
                "original_doc_id": original_doc_id,
                "local_files": [f"{shortcode}_original_{i+1}.jpg" for i in range(len(original_file_ids))],
                "comparison_dir": os.path.abspath(self.comparison_dir)
            }
            
        except Exception as e:
            print(f"\n❌ Fetch failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            if self.client:
                self.client.close()

async def test_advanced_fetcher():
    """Test the advanced Instagram fetcher"""
    
    fetcher = AdvancedInstagramFetcher()
    
    # Test with the carousel post
    shortcode = "C-06IDxOH18"
    
    result = await fetcher.fetch_complete_instagram_post(shortcode)
    
    if result["success"]:
        print(f"\n🎊 SUCCESS! Fetched Instagram carousel:")
        print(f"   📱 Post: {result['shortcode']}")
        print(f"   🖼️  Images: {result['images_saved']}")
        print(f"   💾 GridFS IDs: {result['original_file_ids']}")
        print(f"   📂 Local files: {result['local_files']}")
        print(f"   📄 Document ID: {result['original_doc_id']}")
        
        print(f"\n💡 Now you can run VLM analysis on these original images!")
        
    else:
        print(f"❌ Failed: {result['error']}")
        if "carousel_info" in result:
            print(f"   Carousel info: {result['carousel_info']}")

if __name__ == "__main__":
    asyncio.run(test_advanced_fetcher())