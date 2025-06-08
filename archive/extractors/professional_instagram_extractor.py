#!/usr/bin/env python3
"""
Professional Instagram Extractor
Extract carousel images using Instagram's internal API data like professional tools
"""

import time
import random
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

def extract_professional_carousel(shortcode: str) -> Dict[str, Any]:
    """Extract carousel using Instagram's internal JSON data like professional tools"""
    
    # Setup browser
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    result = {
        "shortcode": shortcode,
        "carousel_images": [],
        "post_type": "unknown",
        "carousel_count": 0,
        "success": False
    }
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Professional extraction: {url}")
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
        
        time.sleep(6)  # Wait for full page load
        
        page_source = driver.page_source
        
        # Strategy 1: Extract Instagram's internal JSON data
        # Look for the main GraphQL data that Instagram uses internally
        json_patterns = [
            # Instagram embeds post data in script tags
            r'window\._sharedData\s*=\s*({.*?});',
            r'window\.__additionalDataLoaded\([^,]+,\s*({.*?})\);',
            # GraphQL data patterns
            r'"graphql":\s*({.*?"shortcode_media".*?})',
            # Newer Instagram data patterns
            r'{"require":\[\["ScheduledServerJS".*?"shortcode_media".*?\]\]\]\}',
        ]
        
        instagram_data = None
        for pattern in json_patterns:
            matches = re.findall(pattern, page_source, re.DOTALL)
            if matches:
                try:
                    # Try to parse the JSON data
                    for match in matches:
                        data = json.loads(match)
                        if 'shortcode_media' in str(data) or 'edge_sidecar_to_children' in str(data):
                            instagram_data = data
                            print(f"   📊 Found Instagram JSON data")
                            break
                    if instagram_data:
                        break
                except json.JSONDecodeError:
                    continue
        
        # Strategy 2: Look for specific carousel data patterns in page source
        if not instagram_data:
            print(f"   🔄 Fallback: Searching for carousel patterns...")
            
            # Look for edge_sidecar_to_children pattern (Instagram's carousel structure)
            sidecar_pattern = r'"edge_sidecar_to_children":\s*{\s*"edges":\s*\[(.*?)\]'
            sidecar_match = re.search(sidecar_pattern, page_source, re.DOTALL)
            
            if sidecar_match:
                print(f"   🎠 Found sidecar data")
                # Extract display_url from each edge
                edges_data = sidecar_match.group(1)
                display_urls = re.findall(r'"display_url":\s*"([^"]+)"', edges_data)
                
                for i, url in enumerate(display_urls):
                    clean_url = url.replace('\\u0026', '&').replace('\\/', '/')
                    result["carousel_images"].append({
                        "src": clean_url,
                        "index": i,
                        "source": "sidecar_edges"
                    })
                
                result["post_type"] = "carousel"
                result["carousel_count"] = len(display_urls)
                
            else:
                # Look for single image pattern
                single_patterns = [
                    r'"GraphImage".*?"display_url":\s*"([^"]+)"',
                    r'"__typename":\s*"GraphImage".*?"display_url":\s*"([^"]+)"'
                ]
                
                for pattern in single_patterns:
                    matches = re.findall(pattern, page_source, re.DOTALL)
                    if matches:
                        clean_url = matches[0].replace('\\u0026', '&').replace('\\/', '/')
                        result["carousel_images"].append({
                            "src": clean_url,
                            "index": 0,
                            "source": "single_image"
                        })
                        result["post_type"] = "single"
                        result["carousel_count"] = 1
                        break
        
        # Strategy 3: If we found JSON data, parse it properly
        if instagram_data:
            print(f"   📊 Parsing Instagram JSON data...")
            
            def find_shortcode_media(obj):
                """Recursively find shortcode_media in nested JSON"""
                if isinstance(obj, dict):
                    if 'shortcode_media' in obj:
                        return obj['shortcode_media']
                    for value in obj.values():
                        found = find_shortcode_media(value)
                        if found:
                            return found
                elif isinstance(obj, list):
                    for item in obj:
                        found = find_shortcode_media(item)
                        if found:
                            return found
                return None
            
            shortcode_media = find_shortcode_media(instagram_data)
            
            if shortcode_media:
                # Check if it's a carousel (sidecar)
                if shortcode_media.get('__typename') == 'GraphSidecar':
                    edges = shortcode_media.get('edge_sidecar_to_children', {}).get('edges', [])
                    result["post_type"] = "carousel"
                    result["carousel_count"] = len(edges)
                    
                    for i, edge in enumerate(edges):
                        node = edge.get('node', {})
                        display_url = node.get('display_url')
                        if display_url:
                            result["carousel_images"].append({
                                "src": display_url,
                                "index": i,
                                "source": "json_sidecar"
                            })
                
                # Single image
                elif shortcode_media.get('__typename') == 'GraphImage':
                    display_url = shortcode_media.get('display_url')
                    if display_url:
                        result["carousel_images"].append({
                            "src": display_url,
                            "index": 0,
                            "source": "json_single"
                        })
                        result["post_type"] = "single"
                        result["carousel_count"] = 1
        
        result["success"] = len(result["carousel_images"]) > 0
        
        print(f"   ✅ Extracted: {result['post_type']} with {len(result['carousel_images'])} images")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        result["error"] = str(e)
        return result
    
    finally:
        driver.quit()

def test_professional_extraction():
    """Test professional extraction on our problem shortcodes"""
    
    test_cases = [
        ("C0wmEEKItfR", 10),  # Should be 10 carousel
        ("C0wysT_LC-L", 1),   # Should be 1 single
        ("C0xFHGOrBN7", 3),   # Should be 3 carousel
        ("C0xLaimIm1B", 1),   # Should be 1 single
        ("C0xMpxwKoxb", 1)    # Should be 1 single
    ]
    
    print("🎯 PROFESSIONAL EXTRACTION TEST")
    print("=" * 60)
    
    for shortcode, expected in test_cases:
        print(f"\n📋 Testing {shortcode} (expected: {expected})")
        print("─" * 40)
        
        result = extract_professional_carousel(shortcode)
        
        actual = len(result["carousel_images"])
        status = "✅" if actual == expected else "❌"
        
        print(f"   {status} Expected: {expected}, Got: {actual}")
        print(f"   Post type: {result['post_type']}")
        print(f"   Success: {result['success']}")
        
        if result["carousel_images"]:
            print(f"   📸 Images:")
            for img in result["carousel_images"]:
                print(f"      {img['index']}: {img['src'][:60]}... (source: {img['source']})")
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")

if __name__ == "__main__":
    test_professional_extraction()