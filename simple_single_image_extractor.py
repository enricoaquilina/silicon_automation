#!/usr/bin/env python3
"""
Simple Single Image Extractor + VLM to Flux Pipeline
Always extracts just the first image from any Instagram post, then generates SiliconSentiments version
"""

import os
import time
import requests
import hashlib
import json
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def setup_browser():
    """Setup Chrome browser with Instagram-friendly settings"""
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1366,768")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def close_popups(driver):
    """Close Instagram popups and modals"""
    print("   🚪 Closing popups...")
    
    # Cookie popup
    try:
        cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Allow all cookies') or contains(text(), 'Accept')]")
        if cookie_btn.is_displayed():
            cookie_btn.click()
            time.sleep(2)
            print("      ✅ Closed cookie popup")
    except:
        pass
    
    # Login popup
    try:
        not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
        if not_now_btn.is_displayed():
            not_now_btn.click()
            time.sleep(2)
            print("      ✅ Closed login popup")
    except:
        pass


def extract_first_image(driver):
    """Extract the first/main image from Instagram post"""
    try:
        # Find main content images
        images = driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn'], img[src*='instagram']")
        
        for img in images:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            
            if (src and 't51.29350-15' in src and 
                'profile_pic' not in src and img.is_displayed()):
                
                # Check if it's a substantial image (not a small UI element)
                try:
                    size = img.size
                    if size['width'] > 200 and size['height'] > 200:
                        return {
                            'url': src,
                            'alt': alt,
                            'width': size['width'],
                            'height': size['height']
                        }
                except:
                    continue
        
        return None
    except Exception as e:
        print(f"      ❌ Error extracting image: {e}")
        return None


def download_image(url, filename, download_dir):
    """Download image with proper headers"""
    if not url:
        return False
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if len(response.content) < 5000:  # Too small
            return False
            
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"      ✅ Downloaded: {filename} ({size:,} bytes)")
        return filepath
        
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False


def run_vlm_to_flux(image_path, shortcode):
    """Run the VLM to Flux pipeline on the extracted image"""
    print(f"\n🎨 Running VLM-to-Flux pipeline...")
    
    try:
        # Import the working VLM pipeline
        import sys
        sys.path.append('/Users/enricoaquilina/Documents/Fraud/silicon_automation')
        
        # Run the VLM pipeline (this is the proven working code)
        vlm_cmd = f'python vlm_to_flux_local_fixed.py --input "{image_path}" --shortcode "{shortcode}"'
        
        print(f"   🔧 Command: {vlm_cmd}")
        result = os.system(vlm_cmd)
        
        if result == 0:
            print(f"   ✅ VLM-to-Flux pipeline completed successfully")
            return True
        else:
            print(f"   ❌ VLM-to-Flux pipeline failed with code {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running VLM pipeline: {e}")
        return False


def extract_and_generate(shortcode):
    """Extract first image from Instagram post and generate SiliconSentiments version"""
    download_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(download_dir, exist_ok=True)
    
    print("🎯 SIMPLE SINGLE IMAGE EXTRACTOR + VLM PIPELINE")
    print(f"Target: {shortcode}")
    print(f"Goal: Extract first image + generate SiliconSentiments version")
    print("=" * 60)
    
    driver = setup_browser()
    
    try:
        # Load Instagram post
        url = f"https://www.instagram.com/p/{shortcode}/"
        print(f"\n📍 Loading: {url}")
        driver.get(url)
        time.sleep(8)
        
        close_popups(driver)
        time.sleep(3)
        
        # Extract first image
        print(f"\n📸 Extracting first image...")
        image_data = extract_first_image(driver)
        
        if image_data:
            print(f"   ✅ Found image: {image_data['width']}x{image_data['height']}")
            print(f"   Alt text: {image_data['alt'][:100]}...")
            
            # Download the image
            filename = f"original_{shortcode}.jpg"
            image_path = download_image(image_data['url'], filename, download_dir)
            
            if image_path:
                print(f"   ✅ Original image saved: {filename}")
                
                # Run VLM-to-Flux pipeline
                vlm_success = run_vlm_to_flux(image_path, shortcode)
                
                # Generate results
                result = {
                    'success': True,
                    'shortcode': shortcode,
                    'original_image': {
                        'filename': filename,
                        'url': image_data['url'],
                        'alt': image_data['alt'],
                        'dimensions': f"{image_data['width']}x{image_data['height']}"
                    },
                    'vlm_pipeline_success': vlm_success,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Save report
                report_file = os.path.join(download_dir, 'single_image_extraction_report.json')
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print("\n" + "=" * 60)
                print("🏆 EXTRACTION + GENERATION RESULTS")
                print("=" * 60)
                print("✅ Original image extracted successfully")
                if vlm_success:
                    print("✅ SiliconSentiments version generated successfully")
                    print("🎉 COMPLETE SUCCESS - Ready for automated posting!")
                else:
                    print("⚠️ VLM generation needs attention")
                    print("📈 Original extraction working perfectly")
                
                return result
            else:
                print(f"   ❌ Failed to download image")
        else:
            print(f"   ❌ No suitable image found")
        
        # Return failure result
        return {
            'success': False,
            'shortcode': shortcode,
            'error': 'No image extracted',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {e}")
        return {
            'success': False,
            'shortcode': shortcode,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
    finally:
        driver.quit()


if __name__ == "__main__":
    # Test with the known carousel post
    shortcode = "C0xFHGOrBN7"
    
    print("🚀 STARTING SIMPLIFIED EXTRACTION + GENERATION")
    print("🎯 Strategy: Extract first image only + VLM pipeline")
    print()
    
    result = extract_and_generate(shortcode)
    
    print("\n" + "=" * 60)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 60)
    
    if result.get('success'):
        print("🎉 SIMPLIFIED PIPELINE WORKING!")
        print("✅ First image extracted successfully")
        if result.get('vlm_pipeline_success'):
            print("✅ SiliconSentiments generation working")
            print("🚀 Ready for production deployment!")
        else:
            print("🔧 VLM pipeline needs debugging")
    else:
        print("🔧 EXTRACTION NEEDS WORK")
        print(f"Error: {result.get('error', 'Unknown')}")
    
    print(f"\n📁 Check results in: downloaded_verify_images/verify_C0xFHGOrBN7/")