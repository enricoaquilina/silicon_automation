#!/usr/bin/env python3
"""
Test Video Model Comparison Framework
- Test the new video model comparison system
- Use existing upscaled images from C0xFHGOrBN7
- Compare Kling v1.6 Pro, Minimax Video-01, Wan2.1, and AnimateDiff
"""

import os
import asyncio
import sys
from video_model_comparison_framework import VideoModelComparator


async def main():
    """Test video model comparison with existing upscaled images"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Test directory with upscaled images
    test_dir = "downloaded_verify_images/verify_C0xFHGOrBN7"
    
    # Find upscaled images from different models
    test_images = []
    for model in ["recraft", "flux", "sdxl", "kandinsky"]:
        model_dir = os.path.join(test_dir, f"{model}_model", "upscaled_images")
        if os.path.exists(model_dir):
            # Get first upscaled image from each model
            images = [f for f in os.listdir(model_dir) if f.endswith("_upscaled.jpg")]
            if images:
                test_images.append(os.path.join(model_dir, images[0]))
    
    if not test_images:
        print(f"❌ No upscaled images found in {test_dir}")
        return
    
    print(f"🎬 VIDEO MODEL COMPARISON TEST")
    print(f"Test Images: {len(test_images)}")
    for img in test_images:
        print(f"   📸 {os.path.basename(img)}")
    
    # Setup output directory
    output_dir = os.path.join(test_dir, "video_model_comparison_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run comparison with working models only
    comparator = VideoModelComparator(replicate_token)
    
    # Test specific models that we know work
    models_to_test = ["kling-v2.0", "minimax-video-01", "wan2.1-i2v", "animate-diff"]
    
    print(f"🚀 Testing models: {', '.join(models_to_test)}")
    print("=" * 60)
    
    # Run individual tests first
    for i, image_path in enumerate(test_images[:2], 1):  # Test first 2 images
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        print(f"\n📸 Testing Image {i}: {image_name}")
        
        prompt = "Transform this digital artwork into a dynamic SiliconSentiments branded animation"
        
        for model_key in models_to_test:
            print(f"\n   🎬 Testing {model_key}...")
            result = await comparator.test_video_model(model_key, image_path, prompt, duration=5)
            
            if result.get("success"):
                print(f"      ✅ Success - {result.get('generation_time', 0):.1f}s")
                if result.get('video_urls'):
                    print(f"      🎥 Video URLs: {len(result['video_urls'])}")
            else:
                print(f"      ❌ Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\n🎉 Individual tests complete!")
    print(f"📁 Check results in: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())