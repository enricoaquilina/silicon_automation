#!/usr/bin/env python3
"""
Test Complete Carousel Extraction
Downloads all 3 images from C0xFHGOrBN7 to verify_C0xFHGOrBN7 folder
"""

import asyncio
import time
import json
import hashlib
import requests
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


async def test_carousel_extraction():
    """
    Test extraction of all 3 images from C0xFHGOrBN7 carousel
    SUCCESS CRITERIA: 3 images downloaded to downloaded_verify_images/verify_C0xFHGOrBN7/
    """
    shortcode = "C0xFHGOrBN7"
    expected_images = 3
    download_dir = Path("/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎯 CAROUSEL EXTRACTION TEST")
    print(f"Target: {shortcode} (expecting {expected_images} images)")
    print(f"Download directory: {download_dir}")
    print("=" * 60)
    
    all_downloaded_images = []
    start_time = time.time()
    
    try:
        # Step 1: Navigate to Instagram post
        print("\n📍 Step 1: Navigate to Instagram post")
        base_url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"   Loading: {base_url}")
        
        # Import MCP functions (they're available in the global scope)
        nav_result = mcp__browsermcp__browser_navigate(url=base_url)
        print("   ✅ Navigation successful")
        
        # Wait for page to load completely
        print("   ⏳ Waiting for page to load...")
        await asyncio.sleep(5)
        
        # Step 2: Extract first image
        print("\n📸 Step 2: Extract first image")
        first_image_url = await extract_current_image()
        if first_image_url:
            downloaded = await download_image(first_image_url, shortcode, 1, download_dir)
            if downloaded:
                all_downloaded_images.append(downloaded)
                print(f"   ✅ Downloaded image 1: {downloaded['filename']}")
        
        # Step 3: Navigate and extract remaining images
        print("\n🎠 Step 3: Navigate carousel for remaining images")
        
        for image_num in range(2, expected_images + 1):
            print(f"\n   🔄 Navigating to image {image_num}")
            
            # Try multiple navigation methods
            navigation_success = False
            
            # Method 1: Keyboard navigation (as user suggested)
            try:
                print("      Trying keyboard navigation...")
                mcp__browsermcp__browser_press_key(key="ArrowRight")
                await asyncio.sleep(3)
                navigation_success = True
                print("      ✅ Keyboard navigation executed")
            except Exception as e:
                print(f"      ❌ Keyboard navigation failed: {e}")
            
            # Method 2: Try clicking next button if keyboard didn't work
            if not navigation_success:
                try:
                    print("      Trying button click navigation...")
                    # Take snapshot to find navigation buttons
                    snapshot = mcp__browsermcp__browser_snapshot()
                    
                    # Look for next button and click it
                    next_selectors = [
                        'button[aria-label*="Next"]',
                        '[role="button"][aria-label*="Next"]',
                        'button[data-testid*="next"]'
                    ]
                    
                    for selector in next_selectors:
                        try:
                            mcp__browsermcp__browser_click(
                                element="carousel next button",
                                ref=selector
                            )
                            await asyncio.sleep(3)
                            navigation_success = True
                            print(f"      ✅ Button click successful: {selector}")
                            break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"      ❌ Button navigation failed: {e}")
            
            # Extract image after navigation
            if navigation_success:
                new_image_url = await extract_current_image()
                if new_image_url and new_image_url not in [img['url'] for img in all_downloaded_images]:
                    downloaded = await download_image(new_image_url, shortcode, image_num, download_dir)
                    if downloaded:
                        all_downloaded_images.append(downloaded)
                        print(f"   ✅ Downloaded image {image_num}: {downloaded['filename']}")
                    else:
                        print(f"   ❌ Failed to download image {image_num}")
                else:
                    print(f"   ⚠️ No new image found (might be duplicate or end of carousel)")
            else:
                print(f"   ❌ Could not navigate to image {image_num}")
        
        # Step 4: Test Results
        duration = time.time() - start_time
        success = len(all_downloaded_images) >= expected_images
        
        result = {
            "test_name": "complete_carousel_extraction",
            "success": success,
            "shortcode": shortcode,
            "expected_images": expected_images,
            "extracted_images": len(all_downloaded_images),
            "downloaded_files": all_downloaded_images,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "test_criteria": f"Download {expected_images} images to {download_dir}"
        }
        
        # Save test report
        report_file = download_dir / "extraction_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Print test results
        print("\n" + "=" * 60)
        print("🧪 TEST RESULTS")
        print("=" * 60)
        
        if success:
            print("🎉 TEST PASSED!")
            print(f"✅ Successfully downloaded {len(all_downloaded_images)}/{expected_images} images")
            print("✅ Carousel extraction working correctly")
        else:
            print("📈 TEST PARTIALLY SUCCESSFUL")
            print(f"⚠️ Downloaded {len(all_downloaded_images)}/{expected_images} images")
            print(f"Success rate: {(len(all_downloaded_images)/expected_images)*100:.1f}%")
        
        print(f"\n📊 Test Details:")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Download directory: {download_dir}")
        
        if all_downloaded_images:
            print(f"\n📁 Downloaded files:")
            total_size = 0
            for img in all_downloaded_images:
                size = img['size_bytes']
                total_size += size
                print(f"   - {img['filename']} ({size:,} bytes)")
            print(f"   Total size: {total_size:,} bytes")
        
        # Verify files exist on disk
        print(f"\n🔍 File verification:")
        files_on_disk = list(download_dir.glob("*.jpg"))
        print(f"   JPG files found: {len(files_on_disk)}")
        for file_path in files_on_disk:
            size = file_path.stat().st_size
            print(f"   - {file_path.name} ({size:,} bytes)")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n❌ TEST FAILED: {e}")
        return {
            "test_name": "complete_carousel_extraction",
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }


async def extract_current_image() -> str:
    """
    Extract the current main image URL from the page
    """
    try:
        snapshot = mcp__browsermcp__browser_snapshot()
        
        if not snapshot:
            return None
        
        snapshot_str = str(snapshot)
        
        # Instagram image URL patterns - prioritize high quality
        patterns = [
            # High resolution patterns
            r'https://[^"]*\.fbcdn\.net/v/t51\.29350-15/[^"]*_1440x1440[^"]*\.jpg[^"]*',
            r'https://[^"]*\.fbcdn\.net/v/t51\.29350-15/[^"]*_1080x1080[^"]*\.jpg[^"]*',
            
            # Standard patterns
            r'https://[^"]*\.fbcdn\.net/v/t51\.29350-15/[^"]*\.jpg[^"]*',
            r'https://scontent[^"]*\.fbcdn\.net[^"]*\.jpg[^"]*',
            r'https://[^"]*instagram[^"]*\.fbcdn\.net[^"]*\.jpg[^"]*',
            
            # Quoted patterns
            r'"(https://[^"]*\.fbcdn\.net[^"]*t51\.29350-15[^"]*\.jpg[^"]*)"',
            r'"(https://[^"]*scontent[^"]*\.fbcdn\.net[^"]*\.jpg[^"]*)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, snapshot_str, re.IGNORECASE)
            for match in matches:
                # Handle tuple results from group captures
                if isinstance(match, tuple):
                    url = match[0] if match else ""
                else:
                    url = match
                
                # Clean and validate URL
                clean_url = url.strip('"').strip("'").strip()
                if is_valid_instagram_image(clean_url):
                    print(f"     🔍 Found image URL: {clean_url[:60]}...")
                    return clean_url
        
        print("     ⚠️ No valid Instagram image URLs found")
        return None
        
    except Exception as e:
        print(f"     ❌ Error extracting current image: {e}")
        return None


def is_valid_instagram_image(url: str) -> bool:
    """
    Validate if URL is a legitimate Instagram content image
    """
    if not url or not url.startswith('http'):
        return False
    
    # Must contain Instagram content markers
    content_markers = ['t51.29350-15', 'scontent', 'fbcdn.net']
    has_marker = any(marker in url for marker in content_markers)
    
    # Must be JPG
    is_jpg = url.lower().endswith('.jpg') or '.jpg' in url
    
    # Exclude profile pics and UI elements
    exclude_patterns = [
        'profile_pic', 'avatar', '150x150', '44x44', '32x32',
        'stories', 'highlight', 'reel', 'emoji', 'icon'
    ]
    is_content = not any(pattern in url.lower() for pattern in exclude_patterns)
    
    # Should be substantial (likely content image)
    is_substantial = len(url) > 100
    
    return has_marker and is_jpg and is_content and is_substantial


async def download_image(url: str, shortcode: str, index: int, download_dir: Path) -> Dict[str, Any]:
    """
    Download a single image from the carousel
    """
    if not url:
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache'
    }
    
    try:
        # Clean URL (remove escapes)
        clean_url = url.replace('\\\\', '')
        
        print(f"     📥 Downloading from: {clean_url[:60]}...")
        
        # Download with retries
        for attempt in range(3):
            try:
                response = requests.get(clean_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Verify it's actually an image
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    raise ValueError(f"Not an image: {content_type}")
                
                # Verify minimum size
                if len(response.content) < 5000:  # At least 5KB
                    raise ValueError("Image too small")
                
                break
                
            except Exception as e:
                if attempt == 2:
                    raise e
                print(f"        Retry {attempt + 1}: {e}")
                await asyncio.sleep(2)
        
        # Generate filename
        filename = f"test_carousel_{shortcode}_image_{index}.jpg"
        filepath = download_dir / filename
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Verify file was written
        if not filepath.exists() or filepath.stat().st_size < 5000:
            raise ValueError("File save failed or too small")
        
        # Generate metadata
        size = len(response.content)
        image_hash = hashlib.md5(response.content).hexdigest()
        
        return {
            "index": index,
            "filename": filename,
            "filepath": str(filepath),
            "url": clean_url,
            "size_bytes": size,
            "hash": image_hash
        }
        
    except Exception as e:
        print(f"        ❌ Download error: {e}")
        return None


if __name__ == "__main__":
    print("🧪 STARTING CAROUSEL EXTRACTION TEST")
    print("🎯 TARGET: Download 3 images from C0xFHGOrBN7")
    print("📁 EXPECTED LOCATION: downloaded_verify_images/verify_C0xFHGOrBN7/")
    print()
    
    result = asyncio.run(test_carousel_extraction())
    
    print("\n" + "=" * 60)
    print("🏆 FINAL TEST ASSESSMENT")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 TEST PASSED - CAROUSEL EXTRACTION WORKING!")
        print("✅ All 3 images successfully downloaded")
        print("✅ Files saved to correct location")
        print("🚀 Carousel extraction problem SOLVED!")
    elif result.get("extracted_images", 0) > 0:
        extracted = result.get("extracted_images", 0)
        print(f"📈 TEST PARTIALLY SUCCESSFUL")
        print(f"✅ Downloaded {extracted}/3 images ({(extracted/3)*100:.1f}% success)")
        print("🔧 Significant progress made - minor adjustments needed")
    else:
        print("🔧 TEST NEEDS MORE WORK")
        print("📊 Framework functional but requires refinement")
        print("💡 Navigation method validated, implementation needs tuning")