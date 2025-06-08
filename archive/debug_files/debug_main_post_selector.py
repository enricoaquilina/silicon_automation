#!/usr/bin/env python3
"""
Debug the main post selector to understand the structure better
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_page_structure(shortcode: str):
    """Debug the page structure to understand selectors"""
    
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
        print(f"🔍 Debugging page structure for: {url}")
        driver.get(url)
        time.sleep(8)
        
        print(f"\n📊 PAGE STRUCTURE ANALYSIS")
        print("=" * 60)
        
        # 1. Check for article elements
        articles = driver.find_elements(By.CSS_SELECTOR, "article")
        print(f"1. Article elements: {len(articles)}")
        for i, article in enumerate(articles):
            class_attr = article.get_attribute("class") or ""
            role_attr = article.get_attribute("role") or ""
            print(f"   Article {i+1}: class='{class_attr[:50]}...', role='{role_attr}'")
        
        # 2. Check for main elements
        mains = driver.find_elements(By.CSS_SELECTOR, "main")
        print(f"\\n2. Main elements: {len(mains)}")
        for i, main in enumerate(mains):
            class_attr = main.get_attribute("class") or ""
            role_attr = main.get_attribute("role") or ""
            print(f"   Main {i+1}: class='{class_attr[:50]}...', role='{role_attr}'")
        
        # 3. Check for all images
        all_imgs = driver.find_elements(By.CSS_SELECTOR, "img")
        content_imgs = []
        for img in all_imgs:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            if "fbcdn.net" in src and "t51.29350-15" in src:
                content_imgs.append({
                    "src": src[:80] + "...",
                    "alt": alt[:60] + "..." if len(alt) > 60 else alt
                })
        
        print(f"\\n3. Content images (all): {len(content_imgs)}")
        for i, img in enumerate(content_imgs):
            print(f"   Image {i+1}: {img['alt']}")
            print(f"            {img['src']}")
        
        # 4. Check images within first article (if exists)
        if articles:
            article_imgs = articles[0].find_elements(By.CSS_SELECTOR, "img")
            article_content_imgs = []
            for img in article_imgs:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                if "fbcdn.net" in src and "t51.29350-15" in src:
                    article_content_imgs.append({
                        "src": src[:80] + "...",
                        "alt": alt[:60] + "..." if len(alt) > 60 else alt
                    })
            
            print(f"\\n4. Content images (in first article): {len(article_content_imgs)}")
            for i, img in enumerate(article_content_imgs):
                print(f"   Article Image {i+1}: {img['alt']}")
                print(f"                     {img['src']}")
        
        # 5. Try alternative main post selector
        main_post_containers = driver.find_elements(By.CSS_SELECTOR, 
            "main article, [role='main'] article, section article")
        print(f"\\n5. Main post containers: {len(main_post_containers)}")
        
        if main_post_containers:
            container_imgs = main_post_containers[0].find_elements(By.CSS_SELECTOR, "img")
            container_content_imgs = []
            for img in container_imgs:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                if "fbcdn.net" in src and "t51.29350-15" in src:
                    container_content_imgs.append({
                        "src": src[:80] + "...",
                        "alt": alt[:60] + "..." if len(alt) > 60 else alt
                    })
            
            print(f"   Container images: {len(container_content_imgs)}")
            for i, img in enumerate(container_content_imgs):
                print(f"   Container Image {i+1}: {img['alt']}")
        
        # 6. Check for any divs that might contain the main post
        main_content_divs = driver.find_elements(By.CSS_SELECTOR, 
            "div[style*='max-width'], div[role='presentation']")
        print(f"\\n6. Potential main content divs: {len(main_content_divs)}")
        
        # 7. Look for the specific pattern of image container divs
        image_container_divs = driver.find_elements(By.CSS_SELECTOR, 
            "div[role='presentation'] img, div[tabindex='-1'] img")
        print(f"\\n7. Images in presentation/tabindex divs: {len(image_container_divs)}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page_structure("C0xFHGOrBN7")