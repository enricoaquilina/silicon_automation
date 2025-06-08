#!/usr/bin/env python3
"""
Debug to find ALL carousel images including no-date ones
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import re

def debug_all_carousel_images(shortcode: str):
    """Debug to see what happens when we DON'T apply strict filtering"""
    
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
        print(f"🔍 Debugging ALL carousel images for: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Handle popups
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        time.sleep(2)
        
        # Check for carousel detection
        carousel_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "button[aria-label*='Next'], button[aria-label*='Previous']")
        is_carousel = len(carousel_buttons) > 0
        print(f"Carousel detected: {is_carousel}")
        
        # Try the container approach first
        main_articles = driver.find_elements(By.CSS_SELECTOR, "main article")
        if main_articles:
            container = main_articles[0]
            print(f"Found main article container")
        else:
            articles = driver.find_elements(By.CSS_SELECTOR, "article") 
            if articles:
                container = articles[0]
                print(f"Found article container")
            else:
                post_containers = driver.find_elements(By.CSS_SELECTOR, "div[role='presentation'][tabindex='-1']")
                if post_containers:
                    container = post_containers[0] 
                    print(f"Found post container")
                else:
                    container = driver
                    print(f"Using fallback: whole page")
        
        # Get all images from container
        img_elements = container.find_elements(By.CSS_SELECTOR, "img")
        all_images = []
        
        for img in img_elements:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            
            if src and ("fbcdn.net" in src or "scontent" in src):
                if ("t51.29350-15" in src and
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                    all_images.append({
                        "src": src,
                        "alt": alt
                    })
        
        print(f"\\nTotal content images in container: {len(all_images)}")
        
        # Group by date WITHOUT strict filtering
        date_groups = defaultdict(list)
        no_date_images = []
        
        for img_data in all_images:
            alt = img_data["alt"]
            date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
            
            if date_matches:
                date = date_matches[0]
                date_groups[date].append(img_data)
            else:
                no_date_images.append(img_data)
        
        print(f"\\nBREAKDOWN BY DATE:")
        for date, imgs in date_groups.items():
            print(f"📅 {date}: {len(imgs)} images")
            for i, img in enumerate(imgs):
                print(f"   {i+1}. {img['alt'][:80]}...")
        
        print(f"\\n📅 NO DATE: {len(no_date_images)} images")
        for i, img in enumerate(no_date_images):
            print(f"   {i+1}. {img['alt'][:80]}...")
        
        # Test what we'd get if we include ALL from first date + all no-date
        if date_groups:
            first_date = list(date_groups.keys())[0]
            potential_carousel = date_groups[first_date] + no_date_images
            print(f"\\n🎠 POTENTIAL FULL CAROUSEL:")
            print(f"   {first_date}: {len(date_groups[first_date])} images")
            print(f"   No-date: {len(no_date_images)} images") 
            print(f"   TOTAL: {len(potential_carousel)} images")
            
            print(f"\\n   All potential carousel images:")
            for i, img in enumerate(potential_carousel):
                print(f"   {i+1}. {img['alt'][:80]}...")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_all_carousel_images("C0xFHGOrBN7")