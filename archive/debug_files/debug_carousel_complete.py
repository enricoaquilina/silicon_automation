#!/usr/bin/env python3
"""
Debug carousel to see all images that should be extracted
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_carousel_complete(shortcode: str):
    """Debug to see all images in carousel"""
    
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
        print(f"🔍 Debugging complete carousel for: {url}")
        driver.get(url)
        time.sleep(8)
        
        # Handle popups
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass
        
        print(f"\n📊 COMPLETE CAROUSEL ANALYSIS")
        print("=" * 60)
        
        # 1. Check all images on page grouped by date
        all_imgs = driver.find_elements(By.CSS_SELECTOR, "img")
        content_imgs_by_date = {}
        
        for img in all_imgs:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            if "fbcdn.net" in src and "t51.29350-15" in src:
                # Extract date from alt text
                import re
                date_matches = re.findall(r'on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                if not date_matches:
                    date_matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', alt)
                
                date = date_matches[0] if date_matches else "unknown"
                
                if date not in content_imgs_by_date:
                    content_imgs_by_date[date] = []
                
                content_imgs_by_date[date].append({
                    "src": src[:80] + "...",
                    "alt": alt[:100] + "..." if len(alt) > 100 else alt
                })
        
        print(f"Images by date:")
        for date, imgs in content_imgs_by_date.items():
            print(f"\\n📅 {date}: {len(imgs)} images")
            for i, img in enumerate(imgs):
                print(f"   {i+1}. {img['alt']}")
                print(f"      {img['src']}")
        
        # 2. Try to navigate carousel if it exists
        carousel_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "button[aria-label*='Next'], button[aria-label*='Previous']")
        
        if carousel_buttons:
            print(f"\\n🎠 CAROUSEL NAVIGATION TEST")
            print("=" * 40)
            print(f"Found {len(carousel_buttons)} carousel navigation buttons")
            
            # Try to click next button multiple times to reveal all carousel images
            next_buttons = [btn for btn in carousel_buttons if 'Next' in btn.get_attribute('aria-label')]
            if next_buttons:
                print(f"Attempting to navigate carousel...")
                for click_num in range(5):  # Try up to 5 clicks
                    try:
                        # Find next button again (it might be recreated)
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Next']")
                        if next_buttons:
                            next_buttons[0].click()
                            time.sleep(2)  # Wait for new image to load
                            print(f"   Clicked next {click_num + 1} times")
                            
                            # Check what images are now visible
                            current_imgs = driver.find_elements(By.CSS_SELECTOR, "img")
                            new_content_imgs = []
                            for img in current_imgs:
                                src = img.get_attribute("src") or ""
                                alt = img.get_attribute("alt") or ""
                                if "fbcdn.net" in src and "t51.29350-15" in src:
                                    new_content_imgs.append({
                                        "src": src[:80] + "...",
                                        "alt": alt[:100] + "..." if len(alt) > 100 else alt
                                    })
                            
                            print(f"      Visible images after click {click_num + 1}: {len(new_content_imgs)}")
                            for img in new_content_imgs:
                                if img not in [item for sublist in content_imgs_by_date.values() for item in sublist]:
                                    print(f"      NEW: {img['alt']}")
                        else:
                            print(f"   No more next buttons found")
                            break
                    except Exception as e:
                        print(f"   Navigation failed: {e}")
                        break
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_carousel_complete("C0xFHGOrBN7")