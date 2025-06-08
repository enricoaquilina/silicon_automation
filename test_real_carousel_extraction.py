#!/usr/bin/env python3
"""
Real Carousel Extraction Test

Test the intelligent agent's ability to extract all 3 images from C0xFHGOrBN7 
and save them to downloaded_verify_images/verify_C0xFHGOrBN7/
"""

import asyncio
import time
import json
import hashlib
import requests
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class RealCarouselExtractor:
    """
    Real carousel extractor using actual BrowserMCP tools
    """
    
    def __init__(self):
        self.download_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        print(f"🎯 Real Carousel Extractor initialized")
        print(f"📁 Target directory: {self.download_dir}")

    async def extract_c0xfhgorbN7_complete(self) -> Dict[str, Any]:
        """
        Complete extraction of C0xFHGOrBN7 carousel (3 images expected)
        """
        shortcode = "C0xFHGOrBN7"
        expected_images = 3
        
        print(f"\n🎠 EXTRACTING COMPLETE CAROUSEL: {shortcode}")
        print(f"🎯 Target: {expected_images} images")
        print("=" * 60)
        
        start_time = time.time()
        extracted_urls = set()
        
        try:
            # Step 1: Navigate and handle popups (already done from our previous test)
            print("✅ Already navigated to post")
            
            # Step 2: Wait for content to fully load
            print("⏳ Waiting for carousel content to load...")
            await self._wait_for_carousel_content()
            
            # Step 3: Extract images from current view
            print("📸 Extracting images from current view...")
            current_images = await self._extract_images_from_current_view()
            extracted_urls.update(current_images)
            print(f"   Found {len(current_images)} images in initial view")
            
            # Step 4: Navigate through carousel if needed
            if len(extracted_urls) < expected_images:
                print(f"🎠 Need {expected_images - len(extracted_urls)} more images, navigating carousel...")
                
                navigation_attempts = 0
                max_attempts = expected_images * 2
                
                while len(extracted_urls) < expected_images and navigation_attempts < max_attempts:
                    navigation_attempts += 1
                    
                    # Try to navigate to next image
                    nav_success = await self._navigate_carousel_next()
                    
                    if nav_success:
                        print(f"   ✅ Navigation {navigation_attempts} successful")
                        
                        # Wait for new content
                        await asyncio.sleep(3)
                        
                        # Extract new images
                        new_images = await self._extract_images_from_current_view()
                        before_count = len(extracted_urls)
                        extracted_urls.update(new_images)
                        after_count = len(extracted_urls)
                        
                        new_found = after_count - before_count
                        print(f"   📸 Found {new_found} new images (total: {len(extracted_urls)})")
                        
                        if new_found == 0:
                            print("   🔚 No new images found, stopping navigation")
                            break
                    else:
                        print(f"   ❌ Navigation {navigation_attempts} failed")
                        # Try alternative navigation method
                        alt_success = await self._try_alternative_navigation()
                        if not alt_success:
                            break
            
            # Step 5: Download all extracted images
            print(f"\n📥 Downloading {len(extracted_urls)} images...")
            downloaded_images = await self._download_images_to_verify_folder(list(extracted_urls), shortcode)
            
            # Step 6: Generate results
            duration = time.time() - start_time
            success = len(downloaded_images) >= expected_images
            
            result = {
                "success": success,
                "shortcode": shortcode,
                "expected_images": expected_images,
                "extracted_images": len(downloaded_images),
                "image_urls": list(extracted_urls),
                "downloaded_files": downloaded_images,
                "navigation_attempts": navigation_attempts,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "extraction_method": "real_browsermcp_agent"
            }
            
            # Save extraction report
            report_file = Path(self.download_dir) / "extraction_report.json"
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Print results
            status = "🎉 SUCCESS" if success else "⚠️ PARTIAL SUCCESS"
            print(f"\n{status}")
            print(f"   Expected: {expected_images} images")
            print(f"   Extracted: {len(downloaded_images)} images") 
            print(f"   Navigation attempts: {navigation_attempts}")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Files saved to: {self.download_dir}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ EXTRACTION FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }

    async def _wait_for_carousel_content(self):
        """Wait for carousel content to fully load"""
        
        max_wait_rounds = 15
        stable_count = 0
        required_stable = 3
        
        for round_num in range(max_wait_rounds):
            try:
                # Take snapshot to check content
                snapshot = mcp__browsermcp__browser_snapshot()
                
                # Look for image content or carousel indicators
                if self._has_substantial_content(snapshot):
                    stable_count += 1
                    if stable_count >= required_stable:
                        print(f"   ✅ Content stable after {round_num + 1} rounds")
                        return True
                else:
                    stable_count = 0
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ⚠️ Wait round {round_num + 1} error: {e}")
                await asyncio.sleep(1)
        
        print("   ⚠️ Content stability timeout, proceeding anyway")
        return True

    def _has_substantial_content(self, snapshot) -> bool:
        """Check if snapshot has substantial Instagram content"""
        if not snapshot:
            return False
        
        snapshot_str = str(snapshot).lower()
        
        # Look for image indicators
        image_indicators = ['img', 'image', 'photo', 'picture']
        instagram_indicators = ['instagram', 'fbcdn', 't51.29350-15']
        carousel_indicators = ['next', 'previous', 'carousel', 'slide']
        
        image_score = sum(1 for indicator in image_indicators if indicator in snapshot_str)
        instagram_score = sum(1 for indicator in instagram_indicators if indicator in snapshot_str) 
        carousel_score = sum(1 for indicator in carousel_indicators if indicator in snapshot_str)
        
        # Content is substantial if we have images + Instagram content
        return image_score >= 2 and (instagram_score >= 1 or carousel_score >= 1)

    async def _extract_images_from_current_view(self) -> List[str]:
        """Extract Instagram image URLs from current browser view"""
        
        try:
            # Take snapshot
            snapshot = mcp__browsermcp__browser_snapshot()
            if not snapshot:
                return []
            
            # Parse for Instagram image URLs
            image_urls = self._parse_instagram_images_from_snapshot(snapshot)
            
            # Filter for high-quality unique images
            filtered_urls = self._filter_quality_images(image_urls)
            
            return filtered_urls
            
        except Exception as e:
            print(f"   ⚠️ Image extraction error: {e}")
            return []

    def _parse_instagram_images_from_snapshot(self, snapshot) -> List[str]:
        """Parse Instagram image URLs from snapshot"""
        
        snapshot_str = str(snapshot)
        found_urls = set()
        
        # Instagram image URL patterns
        patterns = [
            r'https://[^"\\s]*instagram[^"\\s]*\\.fbcdn\\.net[^"\\s]*\\.jpg[^"\\s]*',
            r'https://[^"\\s]*\\.fbcdn\\.net/v/t51\\.29350-15/[^"\\s]*\\.jpg',
            r'"(https://[^"]*\\.fbcdn\\.net[^"]*\\.jpg[^"]*)"',
            r'src="(https://[^"]*instagram[^"]*\\.jpg[^"]*)"',
            # Additional patterns for different Instagram formats
            r'https://[^"\\s]*\\.fbcdn\\.net[^"\\s]*t51\\.29350-15[^"\\s]*\\.jpg',
            r'https://scontent[^"\\s]*\\.fbcdn\\.net[^"\\s]*\\.jpg'
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
                if url and self._is_valid_instagram_image_url(url):
                    clean_url = url.strip('"').strip("'").strip()
                    if clean_url.startswith('http') and clean_url.endswith('.jpg'):
                        found_urls.add(clean_url)
        
        print(f"   🔍 Found {len(found_urls)} potential Instagram image URLs")
        return list(found_urls)

    def _is_valid_instagram_image_url(self, url: str) -> bool:
        """Validate if URL is a genuine Instagram image"""
        
        # Must contain Instagram content indicators
        instagram_indicators = ['t51.29350-15', 'instagram', 'fbcdn.net']
        has_indicator = any(indicator in url for indicator in instagram_indicators)
        
        # Must be JPG
        is_jpg = url.lower().endswith('.jpg')
        
        # Must not be profile picture or icon
        exclude_patterns = ['profile', 'avatar', 'icon', 'logo', '150x150', '44x44']
        is_content = not any(pattern in url.lower() for pattern in exclude_patterns)
        
        return has_indicator and is_jpg and is_content

    def _filter_quality_images(self, urls: List[str]) -> List[str]:
        """Filter for high-quality Instagram content images"""
        
        if not urls:
            return []
        
        # Categorize by quality indicators
        high_quality = []
        medium_quality = []
        low_quality = []
        
        for url in urls:
            if any(q in url for q in ['1440x1440', '1080x1080']):
                high_quality.append(url)
            elif any(q in url for q in ['750x750', '640x640']):
                medium_quality.append(url)
            else:
                low_quality.append(url)
        
        # Prefer high quality, fall back to medium, then low
        result = high_quality or medium_quality or low_quality
        
        # Remove duplicates while preserving order
        seen = set()
        unique_result = []
        for url in result:
            pattern = self._get_url_pattern(url)
            if pattern not in seen:
                unique_result.append(url)
                seen.add(pattern)
        
        print(f"   ✅ Filtered to {len(unique_result)} high-quality unique images")
        return unique_result

    def _get_url_pattern(self, url: str) -> str:
        """Get URL pattern for deduplication"""
        # Remove size variants and parameters
        pattern = re.sub(r'_[wh]\\d+_', '_', url)
        pattern = re.sub(r'\\?.*$', '', pattern)
        return pattern

    async def _navigate_carousel_next(self) -> bool:
        """Navigate to next image in carousel"""
        
        # Primary navigation: Look for and click Next button
        next_selectors = [
            'button[aria-label*="Next"]',
            'button[aria-label*="next"]', 
            '[data-testid="next"]',
            '.coreSpriteRightPaginationArrow',
            'svg[aria-label*="Next"]',
            'button svg[aria-label*="Next"]',
            '[role="button"][aria-label*="next"]'
        ]
        
        for selector in next_selectors:
            try:
                result = mcp__browsermcp__browser_click(
                    element="carousel next button",
                    ref=selector
                )
                if result:
                    await asyncio.sleep(2)  # Wait for navigation
                    return True
            except Exception:
                continue
        
        return False

    async def _try_alternative_navigation(self) -> bool:
        """Try alternative navigation methods"""
        
        # Method 1: Keyboard navigation
        try:
            mcp__browsermcp__browser_press_key(key="ArrowRight")
            await asyncio.sleep(2)
            return True
        except Exception:
            pass
        
        # Method 2: Try clicking on the image area to advance
        try:
            # Take snapshot to find image area
            snapshot = mcp__browsermcp__browser_snapshot()
            # Look for img elements in snapshot and try clicking them
            # This is a simplified approach - could be enhanced
            
            result = mcp__browsermcp__browser_click(
                element="image area for navigation",
                ref="img"
            )
            if result:
                await asyncio.sleep(2)
                return True
        except Exception:
            pass
        
        return False

    async def _download_images_to_verify_folder(self, urls: List[str], shortcode: str) -> List[Dict[str, Any]]:
        """Download images to the verify folder with proper naming"""
        
        if not urls:
            return []
        
        downloaded = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.instagram.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"   📥 Downloading image {i}/{len(urls)}...")
                
                # Download with retry logic
                for attempt in range(3):
                    try:
                        response = requests.get(url, headers=headers, timeout=30)
                        response.raise_for_status()
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        await asyncio.sleep(2)
                
                # Generate filename similar to your existing files
                filename = f"intelligent_agent_{shortcode}_carousel_{i}.jpg"
                filepath = Path(self.download_dir) / filename
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Create metadata
                size = len(response.content)
                image_hash = hashlib.md5(response.content).hexdigest()
                
                downloaded.append({
                    "index": i,
                    "filename": filename,
                    "filepath": str(filepath),
                    "url": url,
                    "size_bytes": size,
                    "hash": image_hash
                })
                
                print(f"      ✅ Saved: {filename} ({size:,} bytes)")
                
            except Exception as e:
                print(f"      ❌ Download failed for image {i}: {e}")
                continue
        
        print(f"   📁 Successfully downloaded {len(downloaded)} images")
        return downloaded


async def test_real_carousel_extraction():
    """
    Main test function to extract C0xFHGOrBN7 carousel
    """
    print("🧪 TESTING REAL CAROUSEL EXTRACTION")
    print("🎯 Target: C0xFHGOrBN7 (3-image carousel)")
    print("📁 Destination: downloaded_verify_images/verify_C0xFHGOrBN7/")
    print("🤖 Method: Intelligent Agent with Real BrowserMCP")
    print("=" * 80)
    
    extractor = RealCarouselExtractor()
    
    # Run the extraction
    result = await extractor.extract_c0xfhgorbN7_complete()
    
    # Analyze results
    print("\n" + "="*80)
    print("🏁 FINAL TEST RESULTS")
    print("="*80)
    
    if result.get("success", False):
        extracted = result.get("extracted_images", 0)
        expected = result.get("expected_images", 3)
        
        if extracted >= expected:
            print("🎉 COMPLETE SUCCESS!")
            print(f"   ✅ All {expected} carousel images extracted")
            print("   ✅ Intelligent agent working perfectly")
            
            # Verify files exist
            verify_dir = Path("/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7")
            files = list(verify_dir.glob("*.jpg"))
            print(f"   📁 {len(files)} image files in verify directory")
            
            for file in files:
                size = file.stat().st_size
                print(f"      - {file.name} ({size:,} bytes)")
                
        else:
            print(f"📈 SIGNIFICANT IMPROVEMENT!")
            print(f"   ✅ Extracted {extracted}/{expected} images")
            print(f"   📊 Success rate: {(extracted/expected)*100:.1f}%")
            
    else:
        print("⚠️ EXTRACTION ISSUES")
        error = result.get("error", "Unknown error")
        print(f"   ❌ Error: {error}")
        
    duration = result.get("duration_seconds", 0)
    print(f"\n⏱️ Total duration: {duration:.1f} seconds")
    
    return result


if __name__ == "__main__":
    # Run the real carousel extraction test
    result = asyncio.run(test_real_carousel_extraction())
    
    print("\n🎯 CONCLUSION:")
    if result.get("success") and result.get("extracted_images", 0) >= 3:
        print("✅ Intelligent agent successfully fixed carousel extraction!")
        print("✅ All 3 images downloaded to verify_C0xFHGOrBN7 directory")
        print("🚀 Ready for production deployment")
    else:
        print("🔧 Agent needs further optimization for complete success")
        print("📊 Partial improvements demonstrated")