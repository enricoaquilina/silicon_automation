#!/usr/bin/env python3
"""
Debug what's in the container that we're finding
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_container_content(shortcode: str):
    """Debug container content"""
    
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
        print(f"🔍 Debugging container content for: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Handle popups
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        time.sleep(2)  # Additional wait
        
        # Test the different container strategies
        print(f"\\n📊 CONTAINER STRATEGIES TEST")
        print("=" * 60)
        
        # Strategy 1: main article
        main_articles = driver.find_elements(By.CSS_SELECTOR, "main article")
        print(f"1. main article: {len(main_articles)} containers")
        if main_articles:
            imgs = main_articles[0].find_elements(By.CSS_SELECTOR, "img")
            content_imgs = [img for img in imgs if "fbcdn.net" in (img.get_attribute("src") or "") and "t51.29350-15" in (img.get_attribute("src") or "")]
            print(f"   Content images: {len(content_imgs)}")
        
        # Strategy 2: article
        articles = driver.find_elements(By.CSS_SELECTOR, "article")
        print(f"2. article: {len(articles)} containers")
        if articles:
            imgs = articles[0].find_elements(By.CSS_SELECTOR, "img")
            content_imgs = [img for img in imgs if "fbcdn.net" in (img.get_attribute("src") or "") and "t51.29350-15" in (img.get_attribute("src") or "")]
            print(f"   Content images: {len(content_imgs)}")
        
        # Strategy 3: div[role='presentation'][tabindex='-1']
        post_containers = driver.find_elements(By.CSS_SELECTOR, "div[role='presentation'][tabindex='-1']")
        print(f"3. div[role='presentation'][tabindex='-1']: {len(post_containers)} containers")
        if post_containers:
            imgs = post_containers[0].find_elements(By.CSS_SELECTOR, "img")
            content_imgs = [img for img in imgs if "fbcdn.net" in (img.get_attribute("src") or "") and "t51.29350-15" in (img.get_attribute("src") or "")]
            print(f"   Content images: {len(content_imgs)}")
            
            # Show what images this container has
            print(f"   Images in this container:")
            for i, img in enumerate(content_imgs[:8]):  # Show first 8
                alt = img.get_attribute("alt") or ""
                src = img.get_attribute("src") or ""
                print(f"      {i+1}. {alt[:80]}...")
                print(f"         {src[:80]}...")
        
        # Strategy 4: Test the selector from production code
        production_selectors = [
            "div[role='presentation'][tabindex='-1']",
            "main > div > div > div",
            "main > div",
            "main div",
            "div[style*='max-width']"
        ]
        
        for i, selector in enumerate(production_selectors, 4):
            containers = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"{i}. {selector}: {len(containers)} containers")
            if containers:
                imgs = containers[0].find_elements(By.CSS_SELECTOR, "img")
                content_imgs = [img for img in imgs if "fbcdn.net" in (img.get_attribute("src") or "") and "t51.29350-15" in (img.get_attribute("src") or "")]
                print(f"   Content images: {len(content_imgs)}")
                
                if len(content_imgs) > 0:
                    print(f"   Sample images from this container:")
                    for j, img in enumerate(content_imgs[:4]):
                        alt = img.get_attribute("alt") or ""
                        print(f"      {j+1}. {alt[:60]}...")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_container_content("C0xFHGOrBN7")