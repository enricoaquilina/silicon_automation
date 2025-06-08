#!/usr/bin/env python3
"""
Debug what the production filtering is actually seeing
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import re

def debug_production_filtering(shortcode: str):
    """Debug exactly what production filtering sees"""
    
    # Setup browser (same as production)
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
        print(f"🔍 Debugging production filtering for: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Handle popups (same as production)
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        time.sleep(random.uniform(8, 12))  # Same as production
        
        # Test the EXACT same container strategy as production
        time.sleep(2)  # Additional wait for article elements to load
        main_articles = driver.find_elements(By.CSS_SELECTOR, "main article")
        container_found = False
        img_elements = []
        
        if main_articles:
            main_article = main_articles[0]
            img_elements = main_article.find_elements(By.CSS_SELECTOR, "img")
            container_found = True
            print(f"Found main article container with {len(img_elements)} images")
        
        if not img_elements:
            articles = driver.find_elements(By.CSS_SELECTOR, "article")
            if articles:
                main_article = articles[0]
                img_elements = main_article.find_elements(By.CSS_SELECTOR, "img")
                container_found = True
                print(f"Found article container with {len(img_elements)} images")
        
        if not img_elements:
            post_containers = driver.find_elements(By.CSS_SELECTOR, 
                "div[role='presentation'][tabindex='-1'], main > div > div > div")
            if post_containers:
                main_container = post_containers[0]
                img_elements = main_container.find_elements(By.CSS_SELECTOR, "img")
                container_found = True
                print(f"Found post container with {len(img_elements)} images")
        
        if not img_elements:
            container_found = False
            print(f"No container found, using position-based filtering")
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        # Process images exactly like production
        main_post_images = []
        for img in img_elements:
            src = img.get_attribute("src")
            alt = img.get_attribute("alt") or ""
            
            if src and ("fbcdn.net" in src or "scontent" in src):
                if ("t51.29350-15" in src and
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                    main_post_images.append({
                        "src": src,
                        "alt": alt
                    })
        
        print(f"\\nRaw images after filtering: {len(main_post_images)}")
        
        # Apply the EXACT same strict filtering as production
        print(f"\\nApplying strict date-based filtering...")
        
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img_data in main_post_images:
            alt = img_data["alt"]
            # EXACT same regex as production
            date_matches = re.findall(r'on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data)
            else:
                # Also check for shorter date patterns (exact same as production)
                simple_date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                if simple_date_matches:
                    date = simple_date_matches[0]
                    date_groups[date].append(img_data)
                else:
                    no_date_images.append(img_data)
        
        print(f"Date groups found: {len(date_groups)}")
        for date, imgs in date_groups.items():
            print(f"   {date}: {len(imgs)} images")
            for img in imgs:
                print(f"      - {img['alt'][:80]}...")
        
        print(f"No-date images: {len(no_date_images)}")
        for img in no_date_images:
            print(f"   - {img['alt'][:80]}...")
        
        # Show the early no-date logic
        if date_groups:
            first_date = list(date_groups.keys())[0]
            main_post_candidates = date_groups[first_date]
            
            # Find early no-date images
            next_date_position = len(main_post_images)
            if len(date_groups) > 1:
                second_date = list(date_groups.keys())[1]
                for i, img in enumerate(main_post_images):
                    if img in date_groups[second_date]:
                        next_date_position = i
                        break
            
            early_no_date = []
            first_date_end = 0
            
            for i, img in enumerate(main_post_images):
                if img in date_groups[first_date]:
                    first_date_end = max(first_date_end, i)
            
            for i, img in enumerate(main_post_images):
                if (img in no_date_images and 
                    i < next_date_position and 
                    i <= first_date_end + 3):
                    early_no_date.append(img)
            
            print(f"\\nEarly no-date detection:")
            print(f"   First date ends at position: {first_date_end}")
            print(f"   Next date starts at position: {next_date_position}")
            print(f"   Early no-date found: {len(early_no_date)}")
            for img in early_no_date:
                print(f"      - {img['alt'][:80]}...")
            
            total_main = len(main_post_candidates) + len(early_no_date)
            print(f"\\nFINAL: {len(main_post_candidates)} from {first_date} + {len(early_no_date)} early no-date = {total_main} total")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    import random
    debug_production_filtering("C0xFHGOrBN7")