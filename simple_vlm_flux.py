#!/usr/bin/env python3
"""
Simple VLM to Flux Pipeline - No MongoDB dependencies
Just processes the extracted image and generates SiliconSentiments version
"""

import os
import asyncio
import aiohttp
import json
import base64
import sys
from datetime import datetime
from PIL import Image


class SimpleVLMFluxPipeline:
    """Simplified VLM-to-Flux pipeline without MongoDB dependencies"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.replicate_api_url = "https://api.replicate.com/v1/predictions"
        
    async def analyze_image_with_blip(self, image_path: str) -> str:
        """Analyze image using BLIP VLM"""
        print(f"🔍 Analyzing image with BLIP VLM...")
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_b64}"
            
            # BLIP analysis payload
            payload = {
                "version": "2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                "input": {
                    "image": data_uri,
                    "caption": True,
                    "question": "Describe this image in detail, focusing on the subject, style, colors, and artistic elements."
                }
            }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Submit prediction
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        raise Exception(f"BLIP submission failed: {response.status}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   📝 BLIP prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            description = result['output']
                            print(f"   ✅ BLIP analysis complete")
                            return description
                        elif result['status'] == 'failed':
                            raise Exception(f"BLIP analysis failed: {result.get('error')}")
                        
                        await asyncio.sleep(2)
                        
        except Exception as e:
            print(f"   ❌ BLIP analysis error: {e}")
            raise e
    
    def create_siliconsentiments_prompt(self, description: str) -> str:
        """Transform description into SiliconSentiments branded prompt"""
        prompt = f"""Create a stunning SiliconSentiments branded artwork inspired by: {description}

Transform this into a futuristic digital art piece featuring:
- Neural network consciousness visualization with glowing nodes and connections
- Cybernetic organism architecture with metallic and organic fusion
- Quantum computing interface elements with holographic displays
- Blockchain reality matrix patterns with geometric precision
- Algorithmic pattern recognition motifs in the background
- Advanced AI aesthetics with neon accents and digital textures
- Holographic data visualization networks flowing through the composition

Style: High-tech digital art, cyberpunk aesthetic, clean futuristic design
Colors: Electric blues, neon purples, silver metallics, glowing whites
Quality: Ultra-detailed, professional digital artwork, 8K resolution
Brand: SiliconSentiments signature aesthetic - where technology meets consciousness"""
        
        return prompt
    
    async def generate_with_flux(self, prompt: str, shortcode: str) -> str:
        """Generate image using Flux Schnell"""
        print(f"🎨 Generating SiliconSentiments artwork with Flux...")
        
        try:
            payload = {
                "version": "f2ab8a5569fcf1a7bc7c28a9fd5a2c2b4d1a7e1c8f8c7b9a0a1b2c3d4e5f6f7",
                "input": {
                    "prompt": prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "jpg",
                    "output_quality": 90,
                    "seed": None,
                    "num_inference_steps": 4
                }
            }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Submit prediction
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        raise Exception(f"Flux submission failed: {response.status}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   🎯 Flux generation submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            image_url = result['output'][0]
                            print(f"   ✅ Flux generation complete")
                            return image_url
                        elif result['status'] == 'failed':
                            raise Exception(f"Flux generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ Flux generation error: {e}")
            raise e
    
    async def download_generated_image(self, url: str, shortcode: str, output_dir: str) -> str:
        """Download the generated image"""
        print(f"💾 Downloading generated image...")
        
        try:
            filename = f"siliconsentiments_{shortcode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(filepath, 'wb') as f:
                            f.write(await response.read())
                        
                        size = os.path.getsize(filepath)
                        print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
                        return filepath
                    else:
                        raise Exception(f"Download failed: {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Download error: {e}")
            raise e
    
    async def process_image(self, image_path: str, shortcode: str, output_dir: str) -> dict:
        """Complete VLM-to-Flux pipeline for a single image"""
        print(f"🚀 VLM-TO-FLUX PIPELINE")
        print(f"Input: {image_path}")
        print(f"Shortcode: {shortcode}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze with BLIP
            description = await self.analyze_image_with_blip(image_path)
            print(f"📝 Description: {description[:100]}...")
            
            # Step 2: Create SiliconSentiments prompt
            prompt = self.create_siliconsentiments_prompt(description)
            print(f"🎯 SiliconSentiments prompt created")
            
            # Step 3: Generate with Flux
            generated_url = await self.generate_with_flux(prompt, shortcode)
            
            # Step 4: Download generated image
            generated_path = await self.download_generated_image(generated_url, shortcode, output_dir)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'shortcode': shortcode,
                'original_image': image_path,
                'generated_image': generated_path,
                'description': description,
                'prompt': prompt,
                'generated_url': generated_url,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n🎉 PIPELINE COMPLETE!")
            print(f"✅ Original analyzed and SiliconSentiments version generated")
            print(f"⏱️ Duration: {duration:.1f}s")
            print(f"💾 Generated: {os.path.basename(generated_path)}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n❌ PIPELINE FAILED: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }


async def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python simple_vlm_flux.py <image_path> <shortcode>")
        return
    
    image_path = sys.argv[1]
    shortcode = sys.argv[2]
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Setup output directory
    output_dir = os.path.dirname(image_path)
    
    # Run pipeline
    pipeline = SimpleVLMFluxPipeline(replicate_token)
    result = await pipeline.process_image(image_path, shortcode, output_dir)
    
    # Save result
    report_path = os.path.join(output_dir, f'vlm_flux_result_{shortcode}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Result saved: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())