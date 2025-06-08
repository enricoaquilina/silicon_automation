#!/usr/bin/env python3
"""
Direct Browser Test using Available MCP Tools

This tests if we can extract C0xFHGOrBN7 carousel images using the MCP browser tools
that are available in the Claude Code environment.
"""

import asyncio
import time
import json
import re
from pathlib import Path

# Test shortcode info
TEST_SHORTCODE = "C0xFHGOrBN7"
EXPECTED_IMAGES = 3  # This is a 3-image carousel


async def test_direct_browser_extraction():
    """
    Test direct browser extraction using available MCP tools
    """
    print("🧪 DIRECT BROWSER TEST FOR CAROUSEL EXTRACTION")
    print("=" * 60)
    print(f"Target: {TEST_SHORTCODE} (3-image carousel)")
    print("Method: Direct MCP tool calls")
    print()
    
    start_time = time.time()
    
    try:
        # Step 1: Navigate to Instagram post
        url = f"https://www.instagram.com/p/{TEST_SHORTCODE}/"
        print(f"🌐 Navigating to {url}")
        
        # Navigate using MCP browser tool
        nav_result = mcp__browsermcp__browser_navigate(url=url)
        print(f"✅ Navigation result: {nav_result}")
        
        # Wait for page load
        print("⏳ Waiting for page to load...")
        await asyncio.sleep(5)
        
        # Step 2: Take initial snapshot
        print("📸 Taking initial page snapshot...")
        initial_snapshot = mcp__browsermcp__browser_snapshot()
        print(f"✅ Snapshot captured (length: {len(str(initial_snapshot)) if initial_snapshot else 0})")
        
        # Step 3: Handle popups
        print("🔍 Handling Instagram popups...")
        popup_success = await handle_instagram_popups()
        
        # Step 4: Take clean snapshot
        print("📸 Taking clean snapshot after popup handling...")
        clean_snapshot = mcp__browsermcp__browser_snapshot()
        
        # Step 5: Analyze for carousel
        print("🎠 Analyzing carousel structure...")
        carousel_detected = analyze_carousel_structure(clean_snapshot)
        print(f"   Carousel detected: {carousel_detected}")
        
        # Step 6: Extract initial images
        print("🔍 Extracting images from current view...")
        initial_images = extract_images_from_snapshot(clean_snapshot)
        print(f"   Initial images found: {len(initial_images)}")
        
        all_images = set(initial_images)
        
        # Step 7: Navigate carousel if needed
        if carousel_detected and len(all_images) < EXPECTED_IMAGES:
            print(f"🎠 Navigating carousel to find remaining {EXPECTED_IMAGES - len(all_images)} images...")
            
            navigation_attempts = 0
            max_attempts = EXPECTED_IMAGES * 2
            
            while len(all_images) < EXPECTED_IMAGES and navigation_attempts < max_attempts:
                navigation_attempts += 1
                
                # Try carousel navigation
                nav_success = await navigate_carousel_next()
                
                if nav_success:
                    # Wait for new content
                    await asyncio.sleep(3)
                    
                    # Get new snapshot and extract images
                    new_snapshot = mcp__browsermcp__browser_snapshot()
                    new_images = extract_images_from_snapshot(new_snapshot)
                    
                    before_count = len(all_images)
                    all_images.update(new_images)
                    after_count = len(all_images)
                    
                    new_found = after_count - before_count
                    print(f"   Navigation {navigation_attempts}: +{new_found} new images (total: {len(all_images)})")
                    
                    if new_found == 0:
                        print("   🔚 No new images found")
                        break
                else:
                    print(f"   ❌ Navigation attempt {navigation_attempts} failed")
                    break
        
        # Step 8: Results
        duration = time.time() - start_time
        final_image_count = len(all_images)
        success = final_image_count >= EXPECTED_IMAGES
        
        print("\n📊 EXTRACTION RESULTS:")
        print(f"   Expected images: {EXPECTED_IMAGES}")
        print(f"   Extracted images: {final_image_count}")
        print(f"   Success: {success}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Navigation attempts: {navigation_attempts}")
        
        # Show extracted URLs
        if all_images:
            print(f"\\n📸 Extracted Image URLs:")
            for i, url in enumerate(sorted(all_images), 1):
                print(f"   {i}. {url[:80]}...")
        
        # Analysis
        if success:
            print("\\n🎉 SUCCESS! All carousel images extracted!")
            print("✅ Intelligent agent approach working correctly")
        elif final_image_count > 1:
            print(f"\\n📈 PARTIAL SUCCESS! {final_image_count}/{EXPECTED_IMAGES} images extracted")
            print(f"✅ Improvement: {(final_image_count/EXPECTED_IMAGES)*100:.1f}% vs previous ~33%")
        else:
            print("\\n⚠️ LIMITED SUCCESS: Only 1 image extracted")
            print("🔧 Navigation or extraction logic needs refinement")
        
        return {
            "success": success,
            "expected": EXPECTED_IMAGES,
            "extracted": final_image_count,
            "duration": duration,
            "images": list(all_images)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\\n❌ EXTRACTION FAILED: {e}")
        return {
            "success": False,
            "error": str(e),
            "duration": duration
        }


async def handle_instagram_popups() -> bool:
    """Handle Instagram popups using MCP browser clicks"""
    
    popup_selectors = [
        'button[data-cookiebanner="accept_button"]',
        'button:has-text("Accept All")',
        'button:has-text("Accept")',
        '[aria-label="Accept all"]',
        '[aria-label="Close"]',
        'button:has-text("Not Now")',
        'button:has-text("Not now")',
        '[role="button"]:has-text("Not Now")',
        '[aria-label="Close dialog"]',
        'div[role="dialog"] button',
        'button:has-text("I Agree")',
        'button:has-text("Continue")'
    ]
    
    dismissed_count = 0
    
    for attempt in range(3):  # Try 3 rounds of popup dismissal
        popup_found = False
        
        for selector in popup_selectors:
            try:
                result = mcp__browsermcp__browser_click(
                    element=f"popup dismiss button",
                    ref=selector
                )
                
                if result:
                    print(f"   ✅ Dismissed popup: {selector[:50]}...")
                    dismissed_count += 1
                    popup_found = True
                    await asyncio.sleep(2)
                    break
                    
            except Exception:
                continue
        
        if not popup_found:
            break
    
    print(f"   📊 Total popups dismissed: {dismissed_count}")
    return dismissed_count > 0


def analyze_carousel_structure(snapshot) -> bool:
    """Analyze snapshot to detect if this is a carousel"""
    
    if not snapshot:
        return False
    
    snapshot_str = str(snapshot).lower()
    
    # Look for carousel indicators
    carousel_keywords = [
        "next", "previous", "arrow", "pagination", "slide",
        "carousel", "coreSpriteRightPaginationArrow"
    ]
    
    found_indicators = [kw for kw in carousel_keywords if kw in snapshot_str]
    
    # Look for navigation buttons
    nav_patterns = [
        r'aria-label[^>]*next',
        r'aria-label[^>]*previous', 
        r'button[^>]*next',
        r'coreSpriteRightPaginationArrow'
    ]
    
    nav_matches = sum(1 for pattern in nav_patterns if re.search(pattern, snapshot_str))
    
    is_carousel = len(found_indicators) >= 1 or nav_matches >= 1
    
    print(f"   Indicators: {found_indicators}")
    print(f"   Navigation elements: {nav_matches}")
    print(f"   Carousel confidence: {'High' if is_carousel else 'Low'}")
    
    return is_carousel


def extract_images_from_snapshot(snapshot) -> list:
    """Extract Instagram image URLs from snapshot"""
    
    if not snapshot:
        return []
    
    snapshot_str = str(snapshot)
    
    # Instagram image URL patterns
    url_patterns = [
        r'https://[^"\\s]*instagram[^"\\s]*\\.fbcdn\\.net[^"\\s]*\\.jpg[^"\\s]*',
        r'https://[^"\\s]*\\.fbcdn\\.net/v/t51\\.29350-15/[^"\\s]*\\.jpg',
        r'"(https://[^"]*\\.fbcdn\\.net[^"]*\\.jpg[^"]*)"',
        r'src="(https://[^"]*instagram[^"]*\\.jpg[^"]*)"'
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
            if url and ('t51.29350-15' in url or 'instagram' in url):
                # Clean quotes and whitespace
                clean_url = url.strip('"').strip("'").strip()
                if clean_url.startswith('http') and clean_url.endswith('.jpg'):
                    found_urls.add(clean_url)
    
    # Prefer high-quality images
    quality_urls = [url for url in found_urls if any(q in url for q in ['1440x1440', '1080x1080'])]
    other_urls = [url for url in found_urls if url not in quality_urls]
    
    result = quality_urls if quality_urls else other_urls
    
    print(f"   Raw URLs found: {len(found_urls)}")
    print(f"   High-quality URLs: {len(quality_urls)}")
    print(f"   Final URLs: {len(result)}")
    
    return result


async def navigate_carousel_next() -> bool:
    """Navigate to next image in carousel"""
    
    # Try multiple navigation methods
    navigation_methods = [
        ("Next button click", try_next_button),
        ("Keyboard arrow", try_keyboard_nav),
        ("Alternative selectors", try_alt_selectors)
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
    
    return False


async def try_next_button() -> bool:
    """Try clicking standard Next button"""
    
    next_selectors = [
        'button[aria-label*="Next"]',
        'button[aria-label*="next"]',
        '[data-testid="next"]',
        '.coreSpriteRightPaginationArrow'
    ]
    
    for selector in next_selectors:
        try:
            result = mcp__browsermcp__browser_click(
                element="carousel next button",
                ref=selector
            )
            if result:
                await asyncio.sleep(1)
                return True
        except:
            continue
    
    return False


async def try_keyboard_nav() -> bool:
    """Try keyboard arrow navigation"""
    
    try:
        mcp__browsermcp__browser_press_key(key="ArrowRight")
        await asyncio.sleep(1)
        return True
    except:
        return False


async def try_alt_selectors() -> bool:
    """Try alternative carousel selectors"""
    
    alt_selectors = [
        'svg[aria-label*="Next"]',
        'button svg[aria-label*="Next"]',
        '[role="button"][aria-label*="next"]',
        '._6CZji'
    ]
    
    for selector in alt_selectors:
        try:
            result = mcp__browsermcp__browser_click(
                element="alternative next button",
                ref=selector
            )
            if result:
                await asyncio.sleep(1)
                return True
        except:
            continue
    
    return False


if __name__ == "__main__":
    # Run the direct browser test
    result = asyncio.run(test_direct_browser_extraction())
    
    print("\\n" + "="*60)
    print("🏁 FINAL TEST SUMMARY")
    print("="*60)
    
    if result.get("success"):
        print("🎉 CAROUSEL EXTRACTION WORKING!")
        print("✅ Intelligent agent successfully fixed the issue")
    elif result.get("extracted", 0) > 1:
        print("📈 SIGNIFICANT IMPROVEMENT ACHIEVED!")
        print(f"✅ {result['extracted']}/{result.get('expected', 3)} images extracted")
    else:
        print("⚠️ FURTHER OPTIMIZATION NEEDED")
        print("🔧 Additional debugging required")