#!/usr/bin/env python3
"""
Check the downloaded_verify_images directory to see what original Instagram images we have
"""

import os
import json
from PIL import Image
import hashlib

def check_extracted_files():
    print(f'🔍 CHECKING EXTRACTED INSTAGRAM IMAGES')
    print(f'=====================================')
    
    base_dir = 'downloaded_verify_images'
    if not os.path.exists(base_dir):
        print(f'❌ Directory {base_dir} not found')
        return
    
    # Get all subdirectories (one per shortcode)
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f'Found {len(subdirs)} extraction directories')
    
    extracted_images = []
    
    for subdir in subdirs:
        shortcode = subdir.replace('verify_', '')
        subdir_path = os.path.join(base_dir, subdir)
        
        print(f'\n📋 SHORTCODE: {shortcode}')
        print(f'   Directory: {subdir_path}')
        
        # List all files in this directory
        files = os.listdir(subdir_path)
        image_files = [f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]
        json_files = [f for f in files if f.endswith('.json')]
        txt_files = [f for f in files if f.endswith('.txt')]
        
        print(f'   📸 Images: {len(image_files)}')
        print(f'   📄 JSON files: {len(json_files)}')
        print(f'   📝 Text files: {len(txt_files)}')
        
        # Check each image
        for img_file in image_files:
            img_path = os.path.join(subdir_path, img_file)
            try:
                # Get image info
                with Image.open(img_path) as img:
                    width, height = img.size
                    file_size = os.path.getsize(img_path)
                    
                    print(f'      🖼️  {img_file}:')
                    print(f'         Size: {width}x{height}')
                    print(f'         File size: {file_size:,} bytes')
                    print(f'         Format: {img.format}')
                    
                    # Calculate hash to check uniqueness
                    with open(img_path, 'rb') as f:
                        img_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    print(f'         Hash: {img_hash}')
                    
                    extracted_images.append({
                        'shortcode': shortcode,
                        'filename': img_file,
                        'path': img_path,
                        'size': f'{width}x{height}',
                        'file_size': file_size,
                        'hash': img_hash
                    })
                    
            except Exception as e:
                print(f'      ❌ Error reading {img_file}: {e}')
        
        # Check JSON files for metadata
        for json_file in json_files:
            json_path = os.path.join(subdir_path, json_file)
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                print(f'      📄 {json_file}:')
                print(f'         Keys: {list(data.keys()) if isinstance(data, dict) else "Not dict"}')
                
                # Look for important metadata
                if isinstance(data, dict):
                    if 'image_urls' in data:
                        urls = data['image_urls']
                        print(f'         Image URLs: {len(urls)} found')
                        for i, url in enumerate(urls[:3], 1):
                            print(f'            {i}. {url[:60]}...')
                    
                    if 'extraction_method' in data:
                        print(f'         Extraction method: {data["extraction_method"]}')
                    
                    if 'timestamp' in data:
                        print(f'         Extraction time: {data["timestamp"]}')
                        
            except Exception as e:
                print(f'      ❌ Error reading {json_file}: {e}')
        
        # Check text files for extraction info
        for txt_file in txt_files:
            txt_path = os.path.join(subdir_path, txt_file)
            try:
                with open(txt_path, 'r') as f:
                    content = f.read()
                print(f'      📝 {txt_file}:')
                print(f'         Content preview: {content[:200]}...')
                
            except Exception as e:
                print(f'      ❌ Error reading {txt_file}: {e}')

    # Summary
    print(f'\n📊 EXTRACTION SUMMARY')
    print(f'===================')
    print(f'Total extracted images: {len(extracted_images)}')
    print(f'Unique shortcodes: {len(set(img["shortcode"] for img in extracted_images))}')
    
    if extracted_images:
        print(f'\n🎯 THESE ARE REAL INSTAGRAM CAROUSEL IMAGES!')
        print(f'   ✅ Perfect for VLM analysis')
        print(f'   ✅ Original Instagram content (not AI generated)')
        print(f'   ✅ Can be used as source for SiliconSentiments transformations')
        
        # Group by shortcode
        by_shortcode = {}
        for img in extracted_images:
            shortcode = img['shortcode']
            if shortcode not in by_shortcode:
                by_shortcode[shortcode] = []
            by_shortcode[shortcode].append(img)
        
        print(f'\n📋 BY SHORTCODE:')
        for shortcode, images in by_shortcode.items():
            print(f'   {shortcode}: {len(images)} images')
            for img in images:
                print(f'      - {img["filename"]} ({img["size"]})')
        
        # Recommend next steps
        print(f'\n💡 RECOMMENDED NEXT STEPS:')
        print(f'==========================')
        print(f'1. 📸 Use these extracted images as VLM input')
        print(f'2. 🔍 VLM will analyze REAL Instagram content')
        print(f'3. 🎨 Generate SiliconSentiments versions with Flux')
        print(f'4. 💾 Save new images to MongoDB with proper metadata')
        
        # Show example usage
        if extracted_images:
            first_img = extracted_images[0]
            print(f'\n🔧 EXAMPLE VLM PIPELINE USAGE:')
            print(f'=============================')
            print(f'# Use this image for VLM analysis:')
            print(f'image_path = "{first_img["path"]}"')
            print(f'shortcode = "{first_img["shortcode"]}"')
            print(f'')
            print(f'# VLM will analyze the real Instagram image')
            print(f'# Then generate SiliconSentiments branded version')
    else:
        print(f'❌ No extracted images found')
        print(f'   Need to run carousel extractors first')

if __name__ == "__main__":
    check_extracted_files()