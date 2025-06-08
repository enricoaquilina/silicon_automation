#!/usr/bin/env python3
"""
Direct URL Extractor - Use the exact gold URLs to download images
"""

import os
import requests
import hashlib
import json
import time

def get_image_hash(filepath):
    """Get hash of image file"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def download_image(url: str, filepath: str, headers: dict) -> bool:
    """Download image with proper headers"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"✅ Downloaded: {os.path.basename(filepath)} ({size} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def main():
    """Download images using the exact gold URLs"""
    print("🎯 DIRECT URL CAROUSEL EXTRACTION")
    print("=" * 60)
    
    shortcode = "C0xFHGOrBN7"
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # The exact URLs found in page source
    gold_urls = [
        "https://instagram.fmla1-2.fna.fbcdn.net/v/t51.29350-15/409688197_950875209793155_6981069157937748850_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0MTF4MTc2NC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-2.fna.fbcdn.net&_nc_cat=103&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=nKihT-cvaB0Q7kNvwFaPmKo&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3ODk3NjY3NTI1Nw%3D%3D.3-ccb7-5&oh=00_AfLzIk4I6XDgLn5XcYZ9y9xsXIxpy2pH3JZ-4Iws2C_NFg&oe=684601F4&_nc_sid=10d13b",
        "https://instagram.fmla1-1.fna.fbcdn.net/v/t51.29350-15/410140938_884927459607866_2818375595357090150_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-1.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=JACK5MYpcWwQ7kNvwFn5oRf&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3ODk1OTgxNDM1Mw%3D%3D.3-ccb7-5&oh=00_AfJ-9OJMvbAW_5CVGUO9y2Sw3cx7lIieC9UnkTL8MHWp5w&oe=684625CF&_nc_sid=10d13b",
        "https://instagram.fmla1-1.fna.fbcdn.net/v/t51.29350-15/410057185_1320618825266899_8930879645133735611_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-1.fna.fbcdn.net&_nc_cat=107&_nc_oc=Q6cZ2QGNDXB6to2K0zZcR93hcPfmGgFrzVDhzgU37s_3QZUCjkiI_eYf-iz1n7lDQpDlvv4&_nc_ohc=VnWDnJY6IQ0Q7kNvwGDRZlH&_nc_gid=GfcyEpAZj1BInpf3SglCnQ&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzI1NjQwNjQ3OTAxMDEwMDEzMA%3D%3D.3-ccb7-5&oh=00_AfIGsEav-ANocS2QStv-gmDWQKyCFzqcywmfbNebcsssjA&oe=68460C28&_nc_sid=10d13b"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.instagram.com/'
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📥 Downloading 3 carousel images using gold URLs...")
    
    downloaded_images = []
    
    # Download each image
    for i, url in enumerate(gold_urls, 1):
        print(f"\n📍 Downloading image {i}/3...")
        
        filename = f"C0xFHGOrBN7_image_{i}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        if download_image(url, filepath, headers):
            image_hash = get_image_hash(filepath)
            downloaded_images.append({
                'index': i,
                'filename': filename,
                'url': url,
                'hash': image_hash,
                'size': os.path.getsize(filepath)
            })
    
    # Compare with gold standard
    print(f"\n🏆 Comparing with gold standard...")
    
    gold_files = ['gold1.jpg', 'gold2.jpg', 'gold3.jpg']
    gold_hashes = {}
    
    for gold_file in gold_files:
        gold_path = os.path.join(output_dir, gold_file)
        if os.path.exists(gold_path):
            gold_hash = get_image_hash(gold_path)
            gold_hashes[gold_file] = gold_hash
            print(f"📋 Gold {gold_file}: {gold_hash[:12]}...")
    
    # Check matches
    matches = 0
    for img in downloaded_images:
        for gold_file, gold_hash in gold_hashes.items():
            if img['hash'] == gold_hash:
                print(f"✅ Perfect match: {img['filename']} = {gold_file}")
                matches += 1
                break
        else:
            print(f"❌ No match for: {img['filename']} ({img['hash'][:12]}...)")
    
    print(f"\n🎉 EXTRACTION COMPLETE!")
    print("=" * 60)
    print(f"📊 Images downloaded: {len(downloaded_images)}")
    print(f"🎯 Perfect matches: {matches}/3")
    
    if downloaded_images:
        print(f"\n📁 Downloaded images:")
        for img in downloaded_images:
            print(f"  {img['index']}. {img['filename']} ({img['size']} bytes)")
    
    # Save results
    results = {
        "shortcode": shortcode,
        "downloaded_images": downloaded_images,
        "gold_matches": matches,
        "success": matches == 3,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    results_path = os.path.join(output_dir, "direct_extraction_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    if matches == 3:
        print(f"🎊 PERFECT SUCCESS: All 3 carousel images match gold standard!")
    else:
        print(f"⚠️ PARTIAL: Only {matches}/3 images match gold standard")
    
    return matches == 3

if __name__ == "__main__":
    main()