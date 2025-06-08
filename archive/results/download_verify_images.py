#!/usr/bin/env python3
"""
Download images physically for verify posts to test improved extraction logic
"""

import os
import requests
import time
from pathlib import Path
from production_instagram_extractor import ProductionInstagramExtractor

def download_image(url: str, filepath: str) -> bool:
    """Download a single image from URL to filepath"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.instagram.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✅ Downloaded: {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to download {os.path.basename(filepath)}: {e}")
        return False

def main():
    # Download remaining shortcodes
    shortcodes = ['C0xMpxwKoxb', 'C0wysT_LC-L', 'C0xLaimIm1B']
    
    print(f"🖼️  Downloading images for {len(shortcodes)} verify posts...")
    
    # Create base download directory (back to original path with fixed extractor)
    base_dir = Path("downloaded_verify_images")
    base_dir.mkdir(exist_ok=True)
    
    # Create extractor instance and setup driver
    extractor = ProductionInstagramExtractor(replicate_token='dummy')
    print("🤖 Setting up Chrome driver...")
    extractor.setup_browser()
    
    total_downloaded = 0
    
    for i, shortcode in enumerate(shortcodes, 1):
        print(f"\n[{i}/{len(shortcodes)}] Processing {shortcode}...")
        
        # Create directory for this post
        post_dir = base_dir / f"verify_{shortcode}"
        post_dir.mkdir(exist_ok=True)
        
        try:
            # Extract image URLs
            image_urls = extractor.extract_image_urls(shortcode)
            
            if not image_urls:
                print(f"  ⚠️  No images found for {shortcode}")
                continue
            
            print(f"  📥 Downloading {len(image_urls)} images...")
            
            # Download each image
            for j, url in enumerate(image_urls, 1):
                # Determine file extension from URL - prefer jpg over heic
                if '.jpg' in url or 'jpg' in url:
                    ext = '.jpg'
                elif '.jpeg' in url or 'jpeg' in url:
                    ext = '.jpeg'
                elif '.png' in url or 'png' in url:
                    ext = '.png'
                else:
                    ext = '.jpg'  # Default to jpg (Instagram should serve jpg versions)
                
                filename = f"{shortcode}_image_{j}{ext}"
                filepath = post_dir / filename
                
                if download_image(url, str(filepath)):
                    total_downloaded += 1
                
                # Small delay between downloads
                time.sleep(0.5)
            
            # Create info file with extraction details
            info_file = post_dir / "extraction_info.txt"
            with open(info_file, 'w') as f:
                f.write(f"Post: {shortcode}\n")
                f.write(f"URL: https://www.instagram.com/p/{shortcode}/\n")
                f.write(f"Images extracted: {len(image_urls)}\n")
                f.write(f"Extraction timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Image URLs:\n")
                for j, url in enumerate(image_urls, 1):
                    f.write(f"{j}. {url}\n")
            
            print(f"  ✅ Downloaded {len(image_urls)} images for {shortcode}")
            
        except Exception as e:
            print(f"  ❌ Failed to process {shortcode}: {e}")
    
    # Cleanup
    if extractor.driver:
        extractor.driver.quit()
    
    print(f"\n🎉 Download complete!")
    print(f"📊 Total images downloaded: {total_downloaded}")
    print(f"📁 Images saved to: {base_dir.absolute()}")
    
    # Show directory structure
    print(f"\n📋 Directory structure:")
    for shortcode in shortcodes:
        post_dir = base_dir / f"verify_{shortcode}"
        if post_dir.exists():
            image_files = list(post_dir.glob("*.jpg")) + list(post_dir.glob("*.jpeg")) + list(post_dir.glob("*.png")) + list(post_dir.glob("*.heic"))
            print(f"  verify_{shortcode}/: {len(image_files)} images")

if __name__ == "__main__":
    main()