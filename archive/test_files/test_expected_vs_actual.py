#!/usr/bin/env python3
"""
Test to verify expected vs actual carousel image counts
"""

import json
import os
from pathlib import Path

def analyze_previous_results():
    """Analyze what our previous extractors found"""
    
    verify_dir = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7"
    
    print("🔍 ANALYZING PREVIOUS EXTRACTION RESULTS")
    print("=" * 60)
    
    # Check all result files
    result_files = list(Path(verify_dir).glob("*results*.json"))
    
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            method = data.get('extraction_method', result_file.name)
            total = data.get('total_extracted', 0)
            
            print(f"📊 {method}:")
            print(f"   Images extracted: {total}")
            
            if 'images' in data:
                print(f"   Image details:")
                for img in data['images'][:5]:  # Show first 5
                    filename = img.get('filename', 'unknown')
                    size = img.get('size', 0)
                    print(f"      • {filename} ({size:,} bytes)")
                    
                if len(data['images']) > 5:
                    print(f"      • ... and {len(data['images']) - 5} more")
            
            print()
            
        except Exception as e:
            print(f"❌ Error reading {result_file.name}: {e}")
    
    # Check what files actually exist
    print(f"📁 ACTUAL FILES IN DIRECTORY:")
    image_files = list(Path(verify_dir).glob("*.jpg"))
    image_files.sort()
    
    print(f"   Total .jpg files: {len(image_files)}")
    
    # Group by prefix
    prefixes = {}
    for img_file in image_files:
        prefix = img_file.name.split('_')[0]
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(img_file)
    
    for prefix, files in prefixes.items():
        print(f"   {prefix}_*: {len(files)} files")
        for f in files:
            size = f.stat().st_size
            print(f"      • {f.name} ({size:,} bytes)")
    
    # Analysis
    print(f"\n📋 ANALYSIS:")
    
    # Find the method that got the most images
    max_images = 0
    best_method = None
    
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            total = data.get('total_extracted', 0)
            if total > max_images:
                max_images = total
                best_method = data.get('extraction_method', result_file.name)
                
        except:
            continue
    
    print(f"   Best performing method: {best_method} ({max_images} images)")
    
    # Check for duplicates by size
    sizes = []
    for img_file in image_files:
        sizes.append(img_file.stat().st_size)
    
    unique_sizes = set(sizes)
    print(f"   Unique file sizes: {len(unique_sizes)} out of {len(image_files)} files")
    
    if len(unique_sizes) < len(image_files):
        print("   ⚠️ Possible duplicates detected!")
        
        # Find duplicates
        size_counts = {}
        for size in sizes:
            size_counts[size] = size_counts.get(size, 0) + 1
        
        for size, count in size_counts.items():
            if count > 1:
                print(f"      Size {size:,} bytes appears {count} times")
    
    # Check if we have evidence of a 3rd image
    original_results_file = Path(verify_dir) / "test_extraction_results.json"
    if original_results_file.exists():
        try:
            with open(original_results_file, 'r') as f:
                original_data = json.load(f)
            
            original_count = original_data.get('total_extracted', 0)
            print(f"   Original test extraction: {original_count} images")
            
            if original_count > max_images:
                print(f"   🚨 DISCREPANCY: Original found {original_count}, best method found {max_images}")
                print(f"   📋 We may be missing {original_count - max_images} images!")
            else:
                print(f"   ✅ Current methods match or exceed original")
                
        except Exception as e:
            print(f"   ❌ Error reading original results: {e}")

def recommend_next_steps():
    """Recommend next steps based on analysis"""
    
    print(f"\n🎯 RECOMMENDED NEXT STEPS:")
    print("=" * 60)
    
    steps = [
        "1. 🔍 Manual verification: Open C0xFHGOrBN7 in browser and count actual carousel images",
        "2. 🔄 Try different waiting strategies: Longer waits after navigation",
        "3. 🎮 Simulate human behavior: Random delays, mouse movements",
        "4. 🔧 Alternative detection: Look for carousel indicators (dots, progress)",
        "5. 📱 Mobile user-agent: Try mobile Instagram interface",
        "6. 🔐 Login approach: Test with authenticated session"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n💡 IMMEDIATE ACTION:")
    print(f"   Create a manual test to verify the actual number of images in C0xFHGOrBN7")
    print(f"   If there really are 3+ images, focus on improving navigation timing")

if __name__ == "__main__":
    analyze_previous_results()
    recommend_next_steps()