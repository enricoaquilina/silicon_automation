#!/usr/bin/env python3
"""
Test VLM Pipeline Setup - Verify local images and show what would be processed
"""

import os
import json
from PIL import Image
from datetime import datetime

def test_pipeline_setup():
    """Test the pipeline setup and show what would be processed"""
    
    print("🔍 VLM-TO-FLUX PIPELINE SETUP TEST")
    print("=" * 50)
    
    base_dir = "downloaded_verify_images"
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        print(f"❌ Directory {base_dir} not found")
        return
    
    print(f"✅ Found directory: {base_dir}")
    
    # Scan for images
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f"📁 Found {len(subdirs)} subdirectories")
    
    image_data = []
    total_cost_estimate = 0
    
    for subdir in subdirs:
        shortcode = subdir.replace('verify_', '')
        subdir_path = os.path.join(base_dir, subdir)
        
        print(f"\n📋 SHORTCODE: {shortcode}")
        print(f"   Directory: {subdir_path}")
        
        # List all files
        files = os.listdir(subdir_path)
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        json_files = [f for f in files if f.endswith('.json')]
        txt_files = [f for f in files if f.endswith('.txt')]
        
        print(f"   📸 Images: {len(image_files)}")
        print(f"   📄 JSON files: {len(json_files)}")
        print(f"   📝 Text files: {len(txt_files)}")
        
        if not image_files:
            print(f"   ⚠️  No images found")
            continue
        
        # Get main image info
        main_image = image_files[0]
        image_path = os.path.join(subdir_path, main_image)
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_type = img.format
            
            file_size = os.path.getsize(image_path)
            
            print(f"   🖼️  Main image: {main_image}")
            print(f"      Size: {width}x{height}")
            print(f"      Format: {format_type}")
            print(f"      File size: {file_size:,} bytes")
            
            # Read metadata if available
            metadata = {}
            if json_files:
                json_path = os.path.join(subdir_path, json_files[0])
                try:
                    with open(json_path, 'r') as f:
                        metadata = json.load(f)
                    print(f"      JSON metadata: {list(metadata.keys())}")
                    if 'extraction_method' in metadata:
                        print(f"      Extraction method: {metadata['extraction_method']}")
                    if 'timestamp' in metadata:
                        print(f"      Extracted: {metadata['timestamp']}")
                except Exception as e:
                    print(f"      ⚠️  Error reading JSON: {e}")
            
            # Read text info if available
            if txt_files:
                txt_path = os.path.join(subdir_path, txt_files[0])
                try:
                    with open(txt_path, 'r') as f:
                        txt_content = f.read()
                    print(f"      Text info: {txt_content[:100]}...")
                except Exception as e:
                    print(f"      ⚠️  Error reading text: {e}")
            
            # Add to processing list
            image_data.append({
                'shortcode': shortcode,
                'image_path': image_path,
                'filename': main_image,
                'size': f'{width}x{height}',
                'file_size': file_size,
                'format': format_type,
                'instagram_url': f'https://instagram.com/p/{shortcode}/',
                'metadata': metadata
            })
            
            # Estimate cost (Flux Schnell = $0.003 per image)
            total_cost_estimate += 0.003
            
        except Exception as e:
            print(f"   ❌ Error reading image: {e}")
    
    # Summary
    print(f"\n📊 PIPELINE SETUP SUMMARY")
    print(f"=" * 50)
    print(f"Images ready for processing: {len(image_data)}")
    print(f"Estimated cost (Flux Schnell): ${total_cost_estimate:.4f}")
    
    if image_data:
        print(f"\n🎯 PROCESSING QUEUE:")
        for i, img in enumerate(image_data, 1):
            print(f"{i}. {img['shortcode']}")
            print(f"   📸 {img['filename']} ({img['size']})")
            print(f"   🔗 {img['instagram_url']}")
            print(f"   💰 Cost: $0.003")
        
        print(f"\n🚀 PIPELINE WORKFLOW:")
        print(f"1. 🔍 VLM Analysis: Extract descriptions from {len(image_data)} original Instagram images")
        print(f"2. 🎨 Brand Prompts: Generate SiliconSentiments style prompts")
        print(f"3. 🖼️  Flux Generation: Create {len(image_data)} new branded images")
        print(f"4. 💾 Save Results: Store in GridFS + local files")
        
        print(f"\n📋 TO RUN THE ACTUAL PIPELINE:")
        print(f"1. Set your Replicate API token:")
        print(f"   export REPLICATE_API_TOKEN='your_token_here'")
        print(f"2. Run the pipeline:")
        print(f"   python vlm_to_flux_local_images.py")
        
        print(f"\n🎉 READY TO START!")
        print(f"You have {len(image_data)} authentic Instagram images ready for VLM analysis.")
        print(f"This will create high-quality SiliconSentiments content based on real Instagram aesthetics.")
        
        # Save setup summary
        setup_summary = {
            "timestamp": datetime.now().isoformat(),
            "images_found": len(image_data),
            "estimated_cost": total_cost_estimate,
            "images": image_data
        }
        
        with open("vlm_pipeline_setup_summary.json", "w") as f:
            json.dump(setup_summary, f, indent=2)
        
        print(f"\n📄 Setup summary saved to: vlm_pipeline_setup_summary.json")
    
    else:
        print(f"❌ No images found for processing")

if __name__ == "__main__":
    test_pipeline_setup()