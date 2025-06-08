#!/usr/bin/env python3
"""
Accurate Instagram Extractor
Use Instagram's GraphQL API structure like 4K Stogram for accurate carousel extraction
"""

import time
import random
import re
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

def extract_accurate_carousel(shortcode: str) -> Dict[str, Any]:
    """Extract carousel using Instagram's GraphQL API like 4K Stogram"""
    
    result = {
        "shortcode": shortcode,
        "carousel_images": [],
        "post_type": "unknown",
        "carousel_count": 0,
        "success": False,
        "method": "unknown"
    }
    
    # Method 1: Try Instagram's ?__a=1 API endpoint (like 4K Stogram uses)
    try:
        print(f"🔍 Method 1: Instagram API endpoint")
        
        # Headers to mimic a real browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Try the ?__a=1 endpoint
        api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1"
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Navigate to the shortcode_media
                if 'graphql' in data and 'shortcode_media' in data['graphql']:
                    media = data['graphql']['shortcode_media']
                    
                    # Check if it's a carousel (GraphSidecar)
                    if media.get('__typename') == 'GraphSidecar':
                        edges = media.get('edge_sidecar_to_children', {}).get('edges', [])
                        result["post_type"] = "carousel"
                        result["carousel_count"] = len(edges)
                        result["method"] = "api_sidecar"
                        
                        for i, edge in enumerate(edges):
                            node = edge.get('node', {})
                            # Get the highest quality image (display_url is usually best)
                            display_url = node.get('display_url')
                            if display_url:
                                result["carousel_images"].append({
                                    "src": display_url,
                                    "index": i,
                                    "type": node.get('__typename', 'unknown')
                                })
                        
                        print(f"   ✅ API: Found {len(edges)} carousel images")
                        
                    # Single image (GraphImage)
                    elif media.get('__typename') == 'GraphImage':
                        display_url = media.get('display_url')
                        if display_url:
                            result["carousel_images"].append({
                                "src": display_url,
                                "index": 0,
                                "type": "GraphImage"
                            })
                            result["post_type"] = "single"
                            result["carousel_count"] = 1
                            result["method"] = "api_single"
                            
                            print(f"   ✅ API: Found single image")
                    
                    # Video post (GraphVideo)
                    elif media.get('__typename') == 'GraphVideo':
                        display_url = media.get('display_url')
                        video_url = media.get('video_url')
                        if display_url:
                            result["carousel_images"].append({
                                "src": display_url,  # Thumbnail
                                "video_src": video_url,  # Actual video
                                "index": 0,
                                "type": "GraphVideo"
                            })
                            result["post_type"] = "video"
                            result["carousel_count"] = 1
                            result["method"] = "api_video"
                            
                            print(f"   ✅ API: Found video post")
                    
                    result["success"] = len(result["carousel_images"]) > 0
                    
                    if result["success"]:
                        return result
                        
            except json.JSONDecodeError:
                print(f"   ❌ API: Invalid JSON response")
            except Exception as e:
                print(f"   ❌ API: Error parsing data: {e}")
        else:
            print(f"   ❌ API: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ API method failed: {e}")
    
    # Method 2: Fallback to browser scraping with better GraphQL parsing
    try:
        print(f"🔍 Method 2: Browser GraphQL extraction")
        
        # Setup browser
        options = Options()
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            driver.get(url)
            
            # Handle cookie popup
            try:
                cookie_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass
            
            time.sleep(6)  # Wait for GraphQL data to load
            
            page_source = driver.page_source
            
            # Look for the specific GraphQL patterns that 4K Stogram uses
            patterns = [
                # Look for edge_sidecar_to_children specifically
                r'"edge_sidecar_to_children":\s*{\s*"edges":\s*\[(.*?)\]\s*}',
                # Look for GraphSidecar data
                r'"__typename":\s*"GraphSidecar".*?"edge_sidecar_to_children":\s*{\s*"edges":\s*\[(.*?)\]',
                # Single image pattern
                r'"__typename":\s*"GraphImage".*?"display_url":\s*"([^"]+)"',
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    if i < 2:  # Carousel patterns
                        print(f"   📊 Browser: Found carousel pattern {i+1}")
                        # Extract display_url from the edges data
                        edges_data = matches[0]
                        urls = re.findall(r'"display_url":\s*"([^"]+)"', edges_data)
                        
                        for j, url in enumerate(urls):
                            clean_url = url.replace('\\u0026', '&').replace('\\/', '/')
                            result["carousel_images"].append({
                                "src": clean_url,
                                "index": j,
                                "type": "carousel_item"
                            })
                        
                        result["post_type"] = "carousel"
                        result["carousel_count"] = len(urls)
                        result["method"] = f"browser_pattern_{i+1}"
                        
                    else:  # Single image pattern
                        print(f"   📷 Browser: Found single image pattern")
                        clean_url = matches[0].replace('\\u0026', '&').replace('\\/', '/')
                        result["carousel_images"].append({
                            "src": clean_url,
                            "index": 0,
                            "type": "single_image"
                        })
                        result["post_type"] = "single"
                        result["carousel_count"] = 1
                        result["method"] = "browser_single"
                    
                    result["success"] = True
                    break
            
            print(f"   ✅ Browser: Extracted {len(result['carousel_images'])} images")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"   ❌ Browser method failed: {e}")
    
    return result

def test_accurate_extraction():
    """Test accurate extraction on our problem shortcodes"""
    
    test_cases = [
        ("C0wmEEKItfR", 10),  # Should be 10 carousel
        ("C0wysT_LC-L", 1),   # Should be 1 single
        ("C0xFHGOrBN7", 3),   # Should be 3 carousel
        ("C0xLaimIm1B", 1),   # Should be 1 single
        ("C0xMpxwKoxb", 1)    # Should be 1 single
    ]
    
    print("🎯 ACCURATE EXTRACTION TEST (4K Stogram Method)")
    print("=" * 60)
    
    for shortcode, expected in test_cases:
        print(f"\n📋 Testing {shortcode} (expected: {expected})")
        print("─" * 40)
        
        result = extract_accurate_carousel(shortcode)
        
        actual = len(result["carousel_images"])
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} Expected: {expected}, Got: {actual}")
        print(f"   Post type: {result['post_type']}")
        print(f"   Method: {result['method']}")
        print(f"   Success: {result['success']}")
        
        if result["carousel_images"]:
            print(f"   📸 Images:")
            for img in result["carousel_images"][:3]:  # Show first 3
                print(f"      {img['index']}: {img['src'][:60]}... (type: {img['type']})")
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")

if __name__ == "__main__":
    test_accurate_extraction()