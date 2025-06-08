#!/usr/bin/env python3
"""
Download the images found by the fixed carousel extractor
"""

import os
import requests
import subprocess
import re
import time

def download_image(url: str, filepath: str) -> bool:
    """Download image with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = os.path.getsize(filepath)
        print(f"  ✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return size > 1000
        
    except Exception as e:
        print(f"  ❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def main():
    print("🔍 Getting fresh carousel extraction results...")
    
    # Run fixed carousel extractor and capture output
    result = subprocess.run(
        ['python', 'fixed_carousel_extractor.py', 'C0xFHGOrBN7'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to run fixed carousel extractor: {result.stderr}")
        return
    
    output = result.stdout
    print("Raw extractor output:")
    print(output)
    
    # Parse URLs from output
    url_pattern = r'https://instagram\.[\w\-\.]+\.fna\.fbcdn\.net/v/[^\s\n)]+\.jpg[^\s\n)]*'
    urls = re.findall(url_pattern, output)
    
    print(f"\\n📊 Found {len(urls)} image URLs")
    
    # Setup output directory
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    os.makedirs(output_dir, exist_ok=True)
    
    # Download images
    downloaded = 0
    for i, url in enumerate(urls[:3], 1):  # Limit to first 3
        filename = f"C0xFHGOrBN7_image_{i}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        print(f"\\n📥 Downloading image {i}/3...")
        print(f"   URL: {url[:100]}...")
        
        if download_image(url, filepath):
            downloaded += 1
        
        time.sleep(1)
    
    # Update extraction info
    info_path = os.path.join(output_dir, "extraction_info.txt")
    with open(info_path, 'w') as f:
        f.write(f"Post: C0xFHGOrBN7\\n")
        f.write(f"URL: https://www.instagram.com/p/C0xFHGOrBN7/\\n")
        f.write(f"Images extracted: {downloaded}\\n")
        f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"Method: Fixed carousel extractor with page source parsing\\n")
        f.write(f"\\nImage URLs:\\n")
        for i, url in enumerate(urls[:downloaded], 1):
            f.write(f"{i}. {url}\\n")
    
    print(f"\\n✅ Successfully downloaded {downloaded} carousel images using fixed extractor")

if __name__ == "__main__":
    main()