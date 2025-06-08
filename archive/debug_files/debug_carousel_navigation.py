#!/usr/bin/env python3
"""
Debug carousel navigation with screenshots and HTML analysis
"""

import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def setup_browser():
    """Setup browser with human-like behavior"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def find_all_buttons(driver):
    """Find all possible button elements that could be Next buttons"""
    print("\\n🔍 Analyzing all buttons on the page...")
    
    buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], [tabindex='0']")
    print(f"   📊 Found {len(buttons)} total clickable elements")
    
    potential_next_buttons = []
    
    for i, btn in enumerate(buttons):
        try:
            if btn.is_displayed():
                aria_label = btn.get_attribute("aria-label") or ""
                class_name = btn.get_attribute("class") or ""
                text_content = btn.text or ""
                
                # Look for Next indicators
                is_next_candidate = any([
                    "next" in aria_label.lower(),
                    "next" in class_name.lower(),
                    "next" in text_content.lower(),
                    "arrow" in class_name.lower(),
                    "chevron" in class_name.lower(),
                    "navigate" in class_name.lower(),
                    "carousel" in class_name.lower()
                ])
                
                if is_next_candidate or i < 20:  # Show first 20 buttons for analysis
                    try:
                        location = btn.location
                        size = btn.size
                        potential_next_buttons.append({
                            "index": i,
                            "aria_label": aria_label,
                            "class": class_name,
                            "text": text_content,
                            "location": location,
                            "size": size,
                            "element": btn,
                            "is_candidate": is_next_candidate
                        })
                        
                        marker = "🎯" if is_next_candidate else "  "
                        print(f"   {marker} Button {i}: aria='{aria_label}' class='{class_name[:50]}' text='{text_content[:20]}'")
                        
                    except Exception as e:
                        print(f"   ❌ Error analyzing button {i}: {e}")
        except:
            continue
    
    return potential_next_buttons

def main():
    print("🔍 Debug carousel navigation for C0xFHGOrBN7...")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup browser
    driver = setup_browser()
    
    try:
        # Load the main post
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"🔍 Loading: {url}")
        driver.get(url)
        
        # Handle initial popups
        try:
            wait = WebDriverWait(driver, 10)
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
            accept_btn.click()
            print("   🍪 Accepted cookies")
            time.sleep(3)
        except:
            print("   🍪 No cookie popup")
        
        # Close any blocking modals
        try:
            modals = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
            for modal in modals:
                if modal.is_displayed():
                    close_btns = modal.find_elements(By.CSS_SELECTOR, "button[aria-label*='Close'], svg[aria-label*='Close']")
                    for btn in close_btns:
                        try:
                            btn.click()
                            print("   ❌ Closed modal")
                            time.sleep(2)
                            break
                        except:
                            continue
        except:
            pass
        
        # Wait for content to load properly
        print("   ⏳ Waiting for content to load...")
        time.sleep(10)
        
        # Take initial screenshot
        screenshot_path = os.path.join(output_dir, "carousel_debug_initial.png")
        driver.save_screenshot(screenshot_path)
        print(f"   📸 Saved initial screenshot: {screenshot_path}")
        
        # Save page source for analysis
        html_path = os.path.join(output_dir, "page_source_debug.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"   💾 Saved page source: {html_path}")
        
        # Find all potential Next buttons
        potential_buttons = find_all_buttons(driver)
        
        # Try the exact XPath first
        exact_xpath = "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[1]/div/div/div/div/div[1]/div/div[1]/div[2]/div/button[2]"
        print(f"\\n🎯 Trying exact XPath: {exact_xpath}")
        try:
            exact_btn = driver.find_element(By.XPATH, exact_xpath)
            print("   ✅ Found element with exact XPath!")
            print(f"   📊 Displayed: {exact_btn.is_displayed()}, Enabled: {exact_btn.is_enabled()}")
            print(f"   📊 Aria-label: '{exact_btn.get_attribute('aria-label')}'")
            print(f"   📊 Class: '{exact_btn.get_attribute('class')}'")
        except Exception as e:
            print(f"   ❌ Exact XPath failed: {e}")
        
        # Try clicking the most promising Next button candidates
        for btn_info in potential_buttons:
            if btn_info["is_candidate"]:
                print(f"\\n🖱️  Trying to click button {btn_info['index']}...")
                try:
                    btn = btn_info["element"]
                    
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(1)
                    
                    # Take screenshot before click
                    screenshot_before = os.path.join(output_dir, f"before_click_button_{btn_info['index']}.png")
                    driver.save_screenshot(screenshot_before)
                    
                    # Click
                    actions = ActionChains(driver)
                    actions.move_to_element(btn).click().perform()
                    print(f"   ✅ Clicked button {btn_info['index']}")
                    
                    # Wait and take screenshot after
                    time.sleep(3)
                    screenshot_after = os.path.join(output_dir, f"after_click_button_{btn_info['index']}.png")
                    driver.save_screenshot(screenshot_after)
                    
                    print(f"   📸 Screenshots saved: {screenshot_before} -> {screenshot_after}")
                    
                    # Check if the page changed (look for different images)
                    # This is a basic check - in practice you'd analyze the images
                    current_images = driver.find_elements(By.CSS_SELECTOR, "img[src*='instagram']")
                    print(f"   📊 Found {len(current_images)} images after click")
                    
                    # Only try the first promising candidate to avoid confusion
                    break
                    
                except Exception as e:
                    print(f"   ❌ Failed to click button {btn_info['index']}: {e}")
        
        # Keep browser open longer for manual inspection
        print("\\n👀 Browser will remain open for 30 seconds for manual inspection...")
        print("   📁 Check the downloaded_verify_images/verify_C0xFHGOrBN7/ folder for screenshots and HTML")
        time.sleep(30)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()