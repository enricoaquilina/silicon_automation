#!/usr/bin/env python3
"""
Test specific shortcode with detailed debugging to see what happens to no-date images
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_detailed_extraction(shortcode: str):
    """Test with detailed debugging"""
    
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
        print(f"🔍 Detailed extraction test: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Handle popups
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        # Check for main article vs fallback
        main_articles = driver.find_elements(By.CSS_SELECTOR, "main article")
        articles = driver.find_elements(By.CSS_SELECTOR, "article")
        
        print(f"Main articles found: {len(main_articles)}")
        print(f"Articles found: {len(articles)}")
        
        # Get images based on container strategy
        if main_articles:
            print(f"Using main article container")
            img_elements = main_articles[0].find_elements(By.CSS_SELECTOR, "img")
        elif articles:
            print(f"Using article container")
            img_elements = articles[0].find_elements(By.CSS_SELECTOR, "img")
        else:
            print(f"Using fallback: all images")
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        # Process images
        all_images = []
        for img in img_elements:
            src = img.get_attribute("src")
            alt = img.get_attribute("alt") or ""
            
            if src and ("fbcdn.net" in src or "scontent" in src):
                if ("t51.29350-15" in src and
                    not any(exclude in src for exclude in ['s150x150', 's320x320', 'profile', 'avatar'])):
                    all_images.append({
                        "src": src,
                        "alt": alt
                    })
        
        print(f"\\n📊 IMAGES FOUND IN CONTAINER: {len(all_images)}")
        
        # Group by date
        from collections import defaultdict
        import re
        
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
        
        print(f"\\nDATE ANALYSIS:")
        for date, imgs in date_groups.items():
            print(f"📅 {date}: {len(imgs)} images")
            for img in imgs:
                print(f"   - {img['alt'][:80]}...")
        
        print(f"\\n📅 NO DATE: {len(no_date_images)} images")
        for img in no_date_images:
            print(f"   - {img['alt'][:80]}...")
        
        # Test what we would get with carousel logic
        if len(date_groups) > 0:
            first_date = list(date_groups.keys())[0]
            carousel_images = date_groups[first_date] + no_date_images
            print(f"\\n🎠 CAROUSEL WOULD GET: {len(carousel_images)} images")
            print(f"   From {first_date}: {len(date_groups[first_date])}")
            print(f"   No-date: {len(no_date_images)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_detailed_extraction("C0xFHGOrBN7")