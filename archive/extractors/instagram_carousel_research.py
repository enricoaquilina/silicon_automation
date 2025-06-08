#!/usr/bin/env python3
"""
Instagram Carousel Research - Understand how carousel navigation actually works
"""

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser for research"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def close_popups(driver):
    """Close popups"""
    popup_selectors = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow')]", 
        "//button[contains(text(), 'Not Now')]",
        "//button[@aria-label='Close']"
    ]
    
    for selector in popup_selectors:
        try:
            wait = WebDriverWait(driver, 3)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            element.click()
            time.sleep(1)
            break
        except:
            continue

def analyze_page_structure(driver, shortcode):
    """Analyze the page structure to understand carousel mechanics"""
    print(f"🔬 Analyzing page structure for {shortcode}")
    
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(8)
    
    close_popups(driver)
    time.sleep(3)
    
    analysis = {
        "shortcode": shortcode,
        "url": url,
        "findings": {}
    }
    
    # 1. Look for carousel indicators
    print("🔍 1. Searching for carousel indicators...")
    indicators = []
    indicator_selectors = [
        "[aria-label*='Go to slide']",
        "[aria-label*='Slide']",
        "[role='tablist']",
        ".carousel-indicators",
        "[data-slide-to]",
        "button[aria-label*='1 of']",
        "button[aria-label*='2 of']",
        "button[aria-label*='3 of']"
    ]
    
    for selector in indicator_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    indicators.append({
                        'selector': selector,
                        'text': elem.text,
                        'aria_label': elem.get_attribute('aria-label'),
                        'class': elem.get_attribute('class'),
                        'id': elem.get_attribute('id')
                    })
        except:
            continue
    
    analysis["findings"]["indicators"] = indicators
    print(f"   Found {len(indicators)} carousel indicators")
    
    # 2. Look for navigation buttons
    print("🔍 2. Searching for navigation buttons...")
    nav_buttons = []
    nav_selectors = [
        "button[aria-label*='Next']",
        "button[aria-label*='Previous']",
        "button[aria-label*='next']", 
        "button[aria-label*='prev']",
        "[role='button'][aria-label*='Next']",
        ".carousel-control-next",
        ".carousel-control-prev"
    ]
    
    for selector in nav_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    nav_buttons.append({
                        'selector': selector,
                        'aria_label': elem.get_attribute('aria-label'),
                        'class': elem.get_attribute('class'),
                        'location': elem.location,
                        'size': elem.size
                    })
        except:
            continue
    
    analysis["findings"]["navigation_buttons"] = nav_buttons
    print(f"   Found {len(nav_buttons)} navigation buttons")
    
    # 3. Analyze image containers
    print("🔍 3. Analyzing image containers...")
    containers = []
    container_selectors = [
        "article",
        "main article",
        "[role='presentation']",
        ".carousel",
        "[data-testid*='carousel']",
        "div[style*='transform']"
    ]
    
    for selector in container_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for i, elem in enumerate(elements):
                if elem.is_displayed():
                    images = elem.find_elements(By.CSS_SELECTOR, "img")
                    carousel_images = [img for img in images if img.get_attribute('src') and 't51.29350-15' in img.get_attribute('src')]
                    
                    containers.append({
                        'selector': selector,
                        'index': i,
                        'total_images': len(images),
                        'carousel_images': len(carousel_images),
                        'class': elem.get_attribute('class'),
                        'style': elem.get_attribute('style')
                    })
        except:
            continue
    
    analysis["findings"]["containers"] = containers
    print(f"   Found {len(containers)} potential containers")
    
    # 4. Check for carousel metadata in page source
    print("🔍 4. Checking page source for carousel metadata...")
    page_source = driver.page_source
    
    metadata = {
        'has_carousel_json': 'carousel' in page_source.lower(),
        'has_slide_count': any(f'{i} of' in page_source for i in range(1, 11)),
        'has_graphql_data': '__additionalDataLoaded' in page_source,
        'has_media_count': 'edge_sidecar_to_children' in page_source
    }
    
    analysis["findings"]["metadata"] = metadata
    print(f"   Metadata analysis complete")
    
    # 5. Try to extract actual carousel structure from GraphQL/JSON
    print("🔍 5. Looking for GraphQL/JSON carousel data...")
    try:
        import re
        
        # Look for GraphQL responses
        graphql_pattern = r'"edge_sidecar_to_children":\s*\{[^}]+\}'
        matches = re.findall(graphql_pattern, page_source)
        
        if matches:
            analysis["findings"]["graphql_carousel_data"] = f"Found {len(matches)} GraphQL carousel references"
        else:
            analysis["findings"]["graphql_carousel_data"] = "No GraphQL carousel data found"
            
    except Exception as e:
        analysis["findings"]["graphql_carousel_data"] = f"Error analyzing GraphQL: {e}"
    
    # 6. Count actual images visible
    print("🔍 6. Counting visible carousel images...")
    try:
        all_images = driver.find_elements(By.CSS_SELECTOR, "img")
        carousel_images = []
        
        for img in all_images:
            src = img.get_attribute('src')
            if (src and 't51.29350-15' in src and 
                not any(ex in src.lower() for ex in ['profile', 'avatar', 's150x150', 's320x320'])):
                carousel_images.append({
                    'src': src[:100] + '...',
                    'alt': img.get_attribute('alt'),
                    'visible': img.is_displayed()
                })
        
        analysis["findings"]["visible_images"] = {
            'count': len(carousel_images),
            'images': carousel_images[:5]  # Show first 5
        }
        
    except Exception as e:
        analysis["findings"]["visible_images"] = f"Error counting images: {e}"
    
    return analysis

def research_both_carousels():
    """Research both test carousels to understand differences"""
    print("🔬 INSTAGRAM CAROUSEL RESEARCH")
    print("=" * 60)
    
    test_cases = [
        {"shortcode": "C0xFHGOrBN7", "expected": 3},
        {"shortcode": "C0wmEEKItfR", "expected": 10}
    ]
    
    driver = setup_browser()
    
    try:
        all_analysis = {}
        
        for test_case in test_cases:
            shortcode = test_case["shortcode"]
            expected_count = test_case["expected"]
            
            print(f"\n🔄 Researching {shortcode} (expecting {expected_count} images)")
            print("-" * 40)
            
            analysis = analyze_page_structure(driver, shortcode)
            all_analysis[shortcode] = analysis
            
            # Print key findings
            print(f"\n📊 Key Findings for {shortcode}:")
            print(f"   Indicators: {len(analysis['findings']['indicators'])}")
            print(f"   Nav Buttons: {len(analysis['findings']['navigation_buttons'])}")
            print(f"   Containers: {len(analysis['findings']['containers'])}")
            
            if 'visible_images' in analysis['findings']:
                img_count = analysis['findings']['visible_images'].get('count', 0)
                print(f"   Visible Images: {img_count}")
            
            # Show navigation buttons details
            if analysis['findings']['navigation_buttons']:
                print(f"   Navigation Button Details:")
                for btn in analysis['findings']['navigation_buttons'][:3]:
                    print(f"     - {btn['aria_label']} at {btn['location']}")
            
            print(f"\n" + "=" * 60)
        
        # Save complete research
        research_path = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/carousel_research_results.json"
        with open(research_path, 'w') as f:
            json.dump(all_analysis, f, indent=2)
        
        print(f"\n📁 Complete research saved to: carousel_research_results.json")
        
        # Generate insights
        print(f"\n💡 RESEARCH INSIGHTS:")
        
        for shortcode, analysis in all_analysis.items():
            expected = 3 if shortcode == "C0xFHGOrBN7" else 10
            visible = analysis['findings'].get('visible_images', {}).get('count', 0)
            nav_buttons = len(analysis['findings']['navigation_buttons'])
            
            print(f"\n{shortcode} ({expected} expected):")
            print(f"   - Visible images: {visible}")
            print(f"   - Navigation buttons: {nav_buttons}")
            
            if nav_buttons > 0:
                print(f"   - Can use button navigation ✅")
            else:
                print(f"   - No navigation buttons found ❌")
            
            if visible >= expected:
                print(f"   - All images visible at once ✅")
            else:
                print(f"   - Need navigation to see all ⚠️")
        
        return all_analysis
        
    finally:
        driver.quit()

if __name__ == "__main__":
    research_both_carousels()