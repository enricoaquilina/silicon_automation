#!/usr/bin/env python3
"""
Compare what we get from container vs fallback for C0xFHGOrBN7
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import re

def compare_container_vs_fallback(shortcode: str):
    """Compare container extraction vs fallback"""
    
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
    
    try:
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"🔍 Comparing container vs fallback for: {url}")
        driver.get(url)
        time.sleep(10)  # Longer wait
        
        # Handle popups
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        time.sleep(2)
        
        def extract_images(container):
            """Extract images from a container"""
            img_elements = container.find_elements(By.CSS_SELECTOR, "img")
            images = []
            
            for img in img_elements:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                if src and ("fbcdn.net" in src or "scontent" in src):
                    if ("t51.29350-15" in src and
                        not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                        images.append({
                            "src": src,
                            "alt": alt
                        })
            return images
        
        def analyze_images(images, source_name):
            """Analyze images and group by date"""
            print(f"\\n📊 {source_name.upper()}: {len(images)} images")
            
            date_groups = defaultdict(list)
            no_date_images = []
            
            for img_data in images:
                alt = img_data["alt"]
                date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                
                if date_matches:
                    date = date_matches[0]
                    date_groups[date].append(img_data)
                else:
                    no_date_images.append(img_data)
            
            for date, imgs in date_groups.items():
                print(f"   📅 {date}: {len(imgs)} images")
            print(f"   📅 NO DATE: {len(no_date_images)} images")
            
            return date_groups, no_date_images
        
        # Test 1: Container approach (try multiple strategies)
        print(f"\\n=== CONTAINER APPROACH ===")
        
        # Strategy 1: main article
        main_articles = driver.find_elements(By.CSS_SELECTOR, "main article")
        if main_articles:
            container_images = extract_images(main_articles[0])
            print(f"Used main article container")
        else:
            # Strategy 2: article
            articles = driver.find_elements(By.CSS_SELECTOR, "article")
            if articles:
                container_images = extract_images(articles[0])
                print(f"Used article container")
            else:
                # Strategy 3: presentation div
                post_containers = driver.find_elements(By.CSS_SELECTOR, "div[role='presentation'][tabindex='-1']")
                if post_containers:
                    container_images = extract_images(post_containers[0])
                    print(f"Used presentation div container")
                else:
                    print("No container found")
                    container_images = []
        
        if container_images:
            container_dates, container_no_date = analyze_images(container_images, "container")
        else:
            container_dates = {}
            container_no_date = []
        
        # Test 2: Fallback approach  
        print(f"\\n=== FALLBACK APPROACH ===")
        fallback_images = extract_images(driver)
        fallback_dates, fallback_no_date = analyze_images(fallback_images, "fallback")
        
        # Compare results
        print(f"\\n=== COMPARISON ===")
        print(f"Container found: {len(container_images)} images")
        print(f"Fallback found: {len(fallback_images)} images")
        print(f"Difference: {len(fallback_images) - len(container_images)} images")
        
        # Show what's missing in container
        if len(fallback_images) > len(container_images):
            print(f"\\nImages in fallback but NOT in container:")
            container_alts = [img["alt"] for img in container_images]
            for img in fallback_images:
                if img["alt"] not in container_alts:
                    print(f"   - {img['alt'][:80]}...")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    compare_container_vs_fallback("C0xFHGOrBN7")