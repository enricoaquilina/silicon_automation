#!/usr/bin/env python3
"""
Deduplicate carousel images and identify the 3 unique images
"""

import os
import hashlib
from PIL import Image
import json

def get_image_hash(filepath):
    """Get hash of image content"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_image_info(filepath):
    """Get image dimensions and file size"""
    try:
        with Image.open(filepath) as img:
            return {
                "size": os.path.getsize(filepath),
                "dimensions": img.size,
                "format": img.format
            }
    except:
        return {"size": 0, "dimensions": (0, 0), "format": "unknown"}

def main():
    output_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Get all downloaded images
    image_files = [f for f in os.listdir(output_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    print(f"🔍 Analyzing {len(image_files)} downloaded images...")
    
    # Group by hash to find duplicates
    hash_groups = {}
    image_info = {}
    
    for filename in image_files:
        filepath = os.path.join(output_dir, filename)
        file_hash = get_image_hash(filepath)
        info = get_image_info(filepath)
        
        if file_hash:
            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append(filename)
            image_info[filename] = info
    
    print(f"📊 Found {len(hash_groups)} unique images from {len(image_files)} files")
    
    # Identify unique images and their duplicates
    unique_images = []
    for i, (hash_val, files) in enumerate(hash_groups.items(), 1):
        # Pick the file with best quality/size as representative
        best_file = max(files, key=lambda f: image_info[f]["size"])
        info = image_info[best_file]
        
        unique_images.append({
            "id": i,
            "representative_file": best_file,
            "hash": hash_val,
            "duplicates": files,
            "duplicate_count": len(files),
            "info": info
        })
        
        print(f"\n🖼️ Unique Image {i}:")
        print(f"   📁 Representative: {best_file}")
        print(f"   📏 Size: {info['size']} bytes, {info['dimensions']}")
        print(f"   🔄 Duplicates: {len(files)} files")
        for dup in files:
            print(f"      - {dup}")
    
    # Save unique images with clear names
    for i, img_data in enumerate(unique_images, 1):
        source_path = os.path.join(output_dir, img_data["representative_file"])
        target_path = os.path.join(output_dir, f"C0xFHGOrBN7_unique_image_{i}.jpg")
        
        # Copy the best quality version
        import shutil
        shutil.copy2(source_path, target_path)
        print(f"✅ Saved unique image {i}: C0xFHGOrBN7_unique_image_{i}.jpg")
    
    # Create analysis report
    report = {
        "shortcode": "C0xFHGOrBN7",
        "total_downloaded": len(image_files),
        "unique_images": len(unique_images),
        "target_images": 3,
        "success": len(unique_images) >= 3,
        "unique_image_analysis": unique_images
    }
    
    report_path = os.path.join(output_dir, "deduplication_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n🎉 DEDUPLICATION COMPLETE!")
    print(f"📊 Result: {len(unique_images)} unique images (target: 3)")
    print(f"{'✅ SUCCESS' if len(unique_images) >= 3 else '❌ INCOMPLETE'}: All carousel images extracted")
    
    return len(unique_images) >= 3

if __name__ == "__main__":
    main()