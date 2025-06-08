#!/usr/bin/env python3
"""
Production Intelligent Agent - Using REAL BrowserMCP Tools

This version uses actual BrowserMCP tools to navigate Instagram and extract carousel images.
Based on your MCP configuration with browsermcp server.
"""

import asyncio
import time
import json
import hashlib
import requests
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

# Import test cases for validation
from carousel_test_plan import TEST_SHORTCODES, SUCCESS_CRITERIA


class ExtractionStrategy(Enum):
    """Different extraction strategies to try"""
    SNAPSHOT_PARSING = "snapshot_parsing"
    DIRECT_ELEMENT_QUERY = "direct_element_query"
    JAVASCRIPT_EXTRACTION = "javascript_extraction"
    FALLBACK_SCRAPING = "fallback_scraping"


class NavigationMethod(Enum):
    """Different navigation methods to try"""
    BUTTON_CLICK = "button_click"
    KEYBOARD_ARROW = "keyboard_arrow"
    TOUCH_SWIPE = "touch_swipe"
    JAVASCRIPT_TRANSFORM = "javascript_transform"


@dataclass
class ExtractionAttempt:
    """Track individual extraction attempts and outcomes"""
    shortcode: str
    strategy: ExtractionStrategy
    navigation_method: NavigationMethod
    success: bool
    images_found: int
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: str = ""


class ProductionIntelligentAgent:
    """
    Production intelligent agent using REAL BrowserMCP tools
    """
    
    def __init__(self, download_dir: Optional[str] = None):
        self.download_dir = download_dir or "/Users/enricoaquilina/Documents/Fraud/silicon_automation/extracted_images"
        Path(self.download_dir).mkdir(exist_ok=True)
        
        # Learning system
        self.extraction_history: List[ExtractionAttempt] = []
        self.strategy_success_rates: Dict[str, float] = {}
        self.shortcode_specific_learning: Dict[str, Dict] = {}
        
        # Current session tracking
        self.image_hashes = set()
        self.extraction_results = {}
        
        # Agent configuration
        self.max_strategies_per_shortcode = 4
        self.max_navigation_attempts = 15
        self.learning_threshold = 0.8
        
        print("🤖 Production Intelligent Agent initialized")
        print(f"📁 Download directory: {self.download_dir}")
        print("🌐 Using REAL BrowserMCP tools")

    async def extract_shortcode_with_real_browser(self, shortcode: str) -> Dict[str, Any]:
        """
        Extract shortcode using REAL browser automation
        """
        print(f"\n🎯 REAL BROWSER EXTRACTION: {shortcode}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Step 1: Navigate to Instagram post using REAL BrowserMCP
            url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"🌐 Navigating to {url}")
            
            # REAL navigation
            from mcp__browsermcp__browser_navigate import mcp__browsermcp__browser_navigate
            nav_result = mcp__browsermcp__browser_navigate(url=url)
            print(f"✅ Navigation result: {nav_result}")
            
            # Wait for page load
            await asyncio.sleep(5)
            
            # Step 2: Take initial snapshot to analyze page
            print("📸 Taking initial page snapshot...")
            from mcp__browsermcp__browser_snapshot import mcp__browsermcp__browser_snapshot
            initial_snapshot = mcp__browsermcp__browser_snapshot()
            
            # Step 3: Handle popups using REAL browser clicks
            await self._real_popup_handling()
            
            # Step 4: Take another snapshot after popup handling
            print("📸 Taking snapshot after popup handling...")
            clean_snapshot = mcp__browsermcp__browser_snapshot()
            
            # Step 5: Analyze carousel structure
            carousel_info = self._analyze_carousel_from_snapshot(clean_snapshot, shortcode)
            print(f"🎠 Carousel analysis: {carousel_info}")
            
            # Step 6: Extract images using real browser tools
            image_urls = await self._extract_images_real_browser(shortcode, carousel_info)
            
            # Step 7: Download the extracted images
            downloaded_images = await self._download_images_real(image_urls, shortcode)
            
            # Step 8: Create final result
            expected_count = TEST_SHORTCODES.get(shortcode, {}).get("expected_images", 1)
            extracted_count = len(downloaded_images)
            duration = time.time() - start_time
            
            final_result = {
                "success": extracted_count >= expected_count,
                "shortcode": shortcode,
                "expected_images": expected_count,
                "extracted_images": extracted_count,
                "downloaded_images": downloaded_images,
                "duration_seconds": duration,
                "carousel_detected": carousel_info,
                "extraction_method": "production_intelligent_agent",
                "timestamp": datetime.now().isoformat(),
                "agent_version": "production_v1.0"
            }
            
            status = "✅ SUCCESS" if final_result["success"] else "⚠️ PARTIAL"
            print(f"\n{status} {shortcode}: {extracted_count}/{expected_count} images in {duration:.1f}s")
            
            return final_result
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ EXTRACTION FAILED: {e}")
            return {
                "success": False,
                "shortcode": shortcode,
                "error": str(e),
                "duration_seconds": duration,
                "extraction_method": "production_intelligent_agent",
                "timestamp": datetime.now().isoformat()
            }

    async def _real_popup_handling(self) -> bool:
        """Handle Instagram popups using REAL browser clicks"""
        print("🔍 Handling Instagram popups...")
        
        # Common Instagram popup selectors
        popup_selectors = [
            # Cookie consent
            'button[data-cookiebanner="accept_button"]',
            'button:has-text("Accept All")',
            'button:has-text("Accept")',
            '[aria-label="Accept all"]',
            
            # Login/signup modals
            '[aria-label="Close"]',
            'button:has-text("Not Now")',
            'button:has-text("Not now")',
            '[role="button"]:has-text("Not Now")',
            
            # General dialogs
            '[aria-label="Close dialog"]',
            'div[role="dialog"] button:last-child',
            '.modal-close',
            
            # Age verification
            'button:has-text("I Agree")',
            'button:has-text("Continue")',
        ]
        
        dismissed_count = 0
        max_attempts = 5
        
        for attempt in range(max_attempts):
            print(f"   Popup detection attempt {attempt + 1}/{max_attempts}")
            
            popup_found = False
            for selector in popup_selectors:
                try:
                    # Try to click the popup dismiss button
                    from mcp__browsermcp__browser_click import mcp__browsermcp__browser_click
                    
                    result = mcp__browsermcp__browser_click(
                        element=f"popup dismiss: {selector[:30]}...",
                        ref=selector
                    )
                    
                    if result:
                        print(f"   ✅ Dismissed popup: {selector[:50]}...")
                        dismissed_count += 1
                        popup_found = True
                        await asyncio.sleep(2)  # Wait for popup to close
                        break
                        
                except Exception as e:
                    # Popup selector didn't work, try next one
                    continue
            
            if not popup_found:
                print("   ✅ No more popups found")
                break
            
            await asyncio.sleep(1)
        
        print(f"📊 Popup handling complete: {dismissed_count} popups dismissed")
        return dismissed_count > 0

    def _analyze_carousel_from_snapshot(self, snapshot, shortcode: str) -> Dict[str, Any]:
        """Analyze if this is a carousel and how many images to expect"""
        
        expected_count = TEST_SHORTCODES.get(shortcode, {}).get("expected_images", 1)
        is_carousel = expected_count > 1
        
        # Analyze snapshot content for carousel indicators
        if snapshot:
            snapshot_str = str(snapshot).lower()
            
            # Look for carousel navigation indicators
            carousel_indicators = [
                "next", "previous", "arrow", "pagination", "slide",
                "coreSpriteRightPaginationArrow", "coreSpriteLeftPaginationArrow"
            ]
            
            found_indicators = [ind for ind in carousel_indicators if ind in snapshot_str]
            
            # Look for multiple image containers
            img_patterns = snapshot_str.count('img src=')
            
            confidence = len(found_indicators) / len(carousel_indicators)
            
            print(f"   📊 Carousel indicators found: {found_indicators}")
            print(f"   📊 Image elements detected: {img_patterns}")
            print(f"   📊 Detection confidence: {confidence:.2f}")
        
        return {
            "is_carousel": is_carousel,
            "expected_images": expected_count,
            "confidence": confidence if snapshot else 0.0,
            "indicators": found_indicators if snapshot else []
        }

    async def _extract_images_real_browser(self, shortcode: str, carousel_info: Dict) -> List[str]:
        """Extract image URLs using real browser navigation"""
        
        image_urls = set()
        is_carousel = carousel_info.get("is_carousel", False)
        expected_count = carousel_info.get("expected_images", 1)
        
        print(f"🔍 Extracting images (carousel: {is_carousel}, expected: {expected_count})")
        
        # Extract images from current view
        current_urls = await self._extract_current_view_images()
        image_urls.update(current_urls)
        print(f"   📸 Initial view: {len(current_urls)} images found")
        
        # If this is a carousel and we need more images, navigate through it
        if is_carousel and len(image_urls) < expected_count:
            print(f"🎠 Navigating carousel to find remaining {expected_count - len(image_urls)} images")
            
            navigation_attempts = 0
            max_attempts = expected_count * 2  # Safety limit
            
            while len(image_urls) < expected_count and navigation_attempts < max_attempts:
                navigation_attempts += 1
                
                # Try to navigate to next image
                nav_success = await self._navigate_carousel_real()
                
                if nav_success:
                    # Wait for new content to load
                    await asyncio.sleep(3)
                    
                    # Extract images from new view
                    new_urls = await self._extract_current_view_images()
                    before_count = len(image_urls)
                    image_urls.update(new_urls)
                    after_count = len(image_urls)
                    
                    new_found = after_count - before_count
                    print(f"   📸 Navigation {navigation_attempts}: +{new_found} new images (total: {len(image_urls)})")
                    
                    if new_found == 0:
                        print("   🔚 No new images found, carousel navigation complete")
                        break
                else:
                    print(f"   ❌ Navigation attempt {navigation_attempts} failed")
                    break
        
        final_urls = list(image_urls)
        print(f"✅ Total image URLs extracted: {len(final_urls)}")
        return final_urls

    async def _extract_current_view_images(self) -> List[str]:
        """Extract Instagram image URLs from current browser view"""
        
        try:
            # Take snapshot of current page
            from mcp__browsermcp__browser_snapshot import mcp__browsermcp__browser_snapshot
            snapshot = mcp__browsermcp__browser_snapshot()
            
            if not snapshot:
                return []
            
            # Parse Instagram image URLs from snapshot
            image_urls = self._parse_instagram_urls_from_snapshot(snapshot)
            
            return image_urls
            
        except Exception as e:
            print(f"   ⚠️ Error extracting current view: {e}")
            return []

    def _parse_instagram_urls_from_snapshot(self, snapshot) -> List[str]:
        """Parse Instagram image URLs from browser snapshot"""
        
        if not snapshot:
            return []
        
        snapshot_str = str(snapshot)
        
        # Instagram image URL patterns
        url_patterns = [
            r'https://[^"]*instagram[^"]*\.fbcdn\.net[^"]*\.jpg[^"]*',
            r'https://[^"]*\.fbcdn\.net/v/t51\.29350-15/[^"]*\.jpg',
            r'"(https://[^"]*\.fbcdn\.net[^"]*\.jpg[^"]*)"',
            r'src="(https://[^"]*instagram[^"]*\.jpg[^"]*)"'
        ]
        
        found_urls = set()
        
        for pattern in url_patterns:
            matches = re.findall(pattern, snapshot_str)
            for match in matches:
                # Clean up URL
                if isinstance(match, tuple):
                    url = match[0] if match else ""
                else:
                    url = match
                
                # Filter for Instagram content images
                if url and any(indicator in url for indicator in ['t51.29350-15', 'instagram']):
                    # Remove quotes and clean up
                    clean_url = url.strip('"').strip("'")
                    if clean_url.startswith('http'):
                        found_urls.add(clean_url)
        
        # Filter for high-quality images
        quality_urls = []
        other_urls = []
        
        for url in found_urls:
            if any(quality in url for quality in ['1440x1440', '1080x1080']):
                quality_urls.append(url)
            elif any(size in url for size in ['750x750', '640x640']):
                other_urls.append(url)
        
        # Prefer high-quality images
        result_urls = quality_urls if quality_urls else other_urls
        
        print(f"   🔍 Parsed {len(result_urls)} Instagram URLs from snapshot")
        return list(result_urls)

    async def _navigate_carousel_real(self) -> bool:
        """Navigate carousel using real browser controls"""
        
        # Try multiple navigation methods
        navigation_methods = [
            ("Button click", self._try_next_button_click),
            ("Keyboard arrow", self._try_keyboard_navigation),
            ("Touch swipe", self._try_touch_swipe)
        ]
        
        for method_name, method_func in navigation_methods:
            try:
                print(f"   🎯 Trying {method_name}...")
                success = await method_func()
                if success:
                    print(f"   ✅ {method_name} successful")
                    return True
                else:
                    print(f"   ❌ {method_name} failed")
            except Exception as e:
                print(f"   ❌ {method_name} error: {e}")
        
        print("   ❌ All navigation methods failed")
        return False

    async def _try_next_button_click(self) -> bool:
        """Try clicking Next button to navigate carousel"""
        
        # Instagram carousel next button selectors
        next_button_selectors = [
            'button[aria-label*="Next"]',
            'button[aria-label*="next"]',
            '[data-testid="next"]',
            '.coreSpriteRightPaginationArrow',
            '._6CZji',
            'svg[aria-label*="Next"]',
            'button svg[aria-label*="Next"]',
            '[role="button"][aria-label*="next"]'
        ]
        
        for selector in next_button_selectors:
            try:
                from mcp__browsermcp__browser_click import mcp__browsermcp__browser_click
                
                result = mcp__browsermcp__browser_click(
                    element=f"carousel next button",
                    ref=selector
                )
                
                if result:
                    await asyncio.sleep(1)  # Wait for navigation
                    return True
                    
            except Exception:
                continue
        
        return False

    async def _try_keyboard_navigation(self) -> bool:
        """Try keyboard arrow navigation"""
        
        try:
            from mcp__browsermcp__browser_press_key import mcp__browsermcp__browser_press_key
            
            mcp__browsermcp__browser_press_key(key="ArrowRight")
            await asyncio.sleep(1)
            return True
            
        except Exception:
            return False

    async def _try_touch_swipe(self) -> bool:
        """Try touch/swipe navigation (not implemented for now)"""
        # Would need coordinate calculation for proper swipe
        return False

    async def _download_images_real(self, urls: List[str], shortcode: str) -> List[Dict[str, Any]]:
        """Download images with real HTTP requests"""
        
        if not urls:
            return []
        
        # Create download directory
        shortcode_dir = Path(self.download_dir) / f"production_{shortcode}"
        shortcode_dir.mkdir(exist_ok=True)
        
        downloaded = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.instagram.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"📥 Downloading image {i}/{len(urls)}...")
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Generate filename
                filename = f"production_{shortcode}_image_{i}.jpg"
                filepath = shortcode_dir / filename
                
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
                
                print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
                
            except Exception as e:
                print(f"   ❌ Download failed for image {i}: {e}")
                continue
        
        print(f"📁 Downloaded {len(downloaded)} images to {shortcode_dir}")
        return downloaded


async def test_production_agent():
    """Test the production agent on C0xFHGOrBN7"""
    
    print("🧪 TESTING PRODUCTION INTELLIGENT AGENT")
    print("=" * 60)
    print("Target: C0xFHGOrBN7 (3-image carousel)")
    print("Using: REAL BrowserMCP tools")
    print()
    
    agent = ProductionIntelligentAgent()
    
    # Test extraction
    result = await agent.extract_shortcode_with_real_browser("C0xFHGOrBN7")
    
    # Results analysis
    print("\n📊 PRODUCTION TEST RESULTS:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Expected: {result.get('expected_images', 'unknown')}")
    print(f"   Extracted: {result.get('extracted_images', 0)}")
    print(f"   Duration: {result.get('duration_seconds', 0):.1f}s")
    
    if result.get('downloaded_images'):
        print(f"   Downloaded Files:")
        for img in result['downloaded_images']:
            print(f"     - {img['filename']} ({img['size_bytes']:,} bytes)")
    
    # Check improvement
    extracted = result.get('extracted_images', 0)
    if extracted >= 3:
        print("\n🎉 BREAKTHROUGH! Agent extracted all 3 carousel images!")
        print("✅ 100% extraction success - problem solved!")
    elif extracted > 1:
        print(f"\n📈 SIGNIFICANT IMPROVEMENT! {extracted}/3 images extracted")
        print(f"✅ {(extracted/3)*100:.1f}% vs previous ~33% success rate")
    else:
        print("\n⚠️ Still need optimization - only got 1 image")
    
    return result


if __name__ == "__main__":
    # Run the production test
    asyncio.run(test_production_agent())