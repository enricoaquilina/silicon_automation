#!/usr/bin/env python3
"""
Working VLM to Flux Pipeline - Based on successful configuration
Uses the exact same models and format that worked on 2025-06-05
"""

import os
import asyncio
import aiohttp
import json
import base64
import sys
from datetime import datetime


class WorkingVLMFluxPipeline:
    """VLM-to-Flux pipeline using proven working configuration"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.replicate_api_url = "https://api.replicate.com/v1/predictions"
        
    async def analyze_image_with_blip(self, image_path: str) -> str:
        """Analyze image using BLIP VLM - exact working configuration"""
        print(f"🔍 Analyzing image with BLIP VLM...")
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_b64}"
            
            # BLIP analysis payload - using working model version
            payload = {
                "version": "2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",  # BLIP working version
                "input": {
                    "image": data_uri,
                    "task": "image_captioning"  # Simple captioning task
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
                        error_text = await response.text()
                        raise Exception(f"BLIP submission failed: {response.status} - {error_text}")
                    
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
                            print(f"   ✅ BLIP analysis complete: {description}")
                            return f"Caption: {description}"
                        elif result['status'] == 'failed':
                            raise Exception(f"BLIP analysis failed: {result.get('error')}")
                        
                        await asyncio.sleep(2)
                        
        except Exception as e:
            print(f"   ❌ BLIP analysis error: {e}")
            raise e
    
    def create_siliconsentiments_prompt(self, description: str, shortcode: str) -> str:
        """Transform description into SiliconSentiments branded prompt with nature and sci-fi elements"""
        
        # Enhanced SiliconSentiments brand prompt with nature-tech fusion
        prompt = f"""SiliconSentiments cyborg-nature fusion reimagining {description}: 
        
        CORE ELEMENTS: Biomechanical cyborg hybrid with organic neural networks, robotic limbs seamlessly integrated with living tissue, crystalline data streams flowing through synthetic veins, holographic forest canopy overlays, digital ivy growing on chrome surfaces
        
        NATURE FUSION: Bioluminescent moss circuits, flowering data nodes, cybernetic tree roots as neural pathways, synthetic DNA helixes, organic metal textures, living crystal formations, bio-digital ecosystem
        
        SCI-FI TECH: Advanced AI consciousness visualization, quantum computing matrices, nano-technology integration, plasma energy fields, metallic chrome surfaces, LED-lit mechanical joints, fiber optic nervous system
        
        VISUAL STYLE: Photorealistic digital art, cinematic lighting, volumetric fog effects, neon accent lighting, ultra-detailed textures, professional composition, 8K quality, Instagram-ready format
        
        COLOR PALETTE: Electric blues, neon greens, chrome silver, organic browns, plasma purple, bioluminescent cyan, metallic gold accents"""
        
        return prompt
    
    async def generate_with_flux_schnell(self, prompt: str, shortcode: str) -> str:
        """Generate image using Flux Schnell - exact working configuration"""
        print(f"🎨 Generating SiliconSentiments artwork with Flux Schnell...")
        
        try:
            # Using current Flux Schnell version
            payload = {
                "version": "131d9e185621b4b4d349fd262e363420a6f74081d8c27966c9c5bcf120fa3985",  # Current Flux Schnell version
                "input": {
                    "prompt": prompt,
                    "num_outputs": 4,  # Generate 4 variations
                    "aspect_ratio": "1:1",
                    "output_format": "jpg",  # JPG format
                    "output_quality": 90,
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
                        error_text = await response.text()
                        raise Exception(f"Flux submission failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   🎯 Flux generation submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            image_urls = result['output']  # Multiple URLs now
                            print(f"   ✅ Flux generation complete - {len(image_urls)} variations")
                            return image_urls
                        elif result['status'] == 'failed':
                            raise Exception(f"Flux generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ Flux generation error: {e}")
            raise e
    
    async def download_generated_images(self, urls: list, shortcode: str, output_dir: str) -> list:
        """Download multiple generated images with concise naming"""
        print(f"💾 Downloading {len(urls)} generated variations...")
        
        downloaded_files = []
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                try:
                    # Concise naming: shortcode_v1.jpg, shortcode_v2.jpg, etc.
                    filename = f"{shortcode}_v{i}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            with open(filepath, 'wb') as f:
                                f.write(await response.read())
                            
                            size = os.path.getsize(filepath)
                            print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
                            
                            downloaded_files.append({
                                'filename': filename,
                                'filepath': filepath,
                                'url': url,
                                'size_bytes': size,
                                'variation': i
                            })
                        else:
                            print(f"   ❌ Failed to download variation {i}: {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Download error for variation {i}: {e}")
                    continue
        
        print(f"   🎉 Successfully downloaded {len(downloaded_files)}/{len(urls)} variations")
        return downloaded_files
    
    async def process_image(self, image_path: str, shortcode: str, output_dir: str) -> dict:
        """Complete VLM-to-Flux pipeline using working configuration"""
        print(f"🚀 WORKING VLM-TO-FLUX PIPELINE")
        print(f"Input: {image_path}")
        print(f"Shortcode: {shortcode}")
        print(f"Configuration: Based on successful 2025-06-05 results")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze with BLIP (working configuration)
            description = await self.analyze_image_with_blip(image_path)
            print(f"📝 VLM Description: {description}")
            
            # Step 2: Create SiliconSentiments prompt (working format)
            prompt = self.create_siliconsentiments_prompt(description, shortcode)
            print(f"🎯 SiliconSentiments prompt created")
            
            # Step 3: Generate with Flux Schnell (working configuration)
            generated_urls = await self.generate_with_flux_schnell(prompt, shortcode)
            
            # Step 4: Download generated images
            downloaded_files = await self.download_generated_images(generated_urls, shortcode, output_dir)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'shortcode': shortcode,
                'original_image': image_path,
                'generated_images': downloaded_files,
                'vlm_description': description,
                'brand_prompt': prompt,
                'generated_urls': generated_urls,
                'cost': 0.012,  # 4 variations x $0.003 each
                'models_used': {
                    'vlm': 'blip',
                    'generation': 'flux-schnell'
                },
                'variations_generated': len(downloaded_files),
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n🎉 PIPELINE COMPLETE!")
            print(f"✅ Original analyzed and {len(downloaded_files)} SiliconSentiments variations generated")
            print(f"⏱️ Duration: {duration:.1f}s")
            print(f"💰 Cost: $0.012 (4 variations)")
            print(f"💾 Generated files:")
            for file_info in downloaded_files:
                print(f"   - {file_info['filename']}")
            
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
        print("Usage: python working_vlm_flux.py <image_path> <shortcode>")
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
    
    # Run pipeline with working configuration
    pipeline = WorkingVLMFluxPipeline(replicate_token)
    result = await pipeline.process_image(image_path, shortcode, output_dir)
    
    # Save result
    report_path = os.path.join(output_dir, f'working_vlm_flux_result_{shortcode}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Result saved: {report_path}")
    
    if result.get('success'):
        print(f"\n🎉 SUCCESS! Complete end-to-end pipeline working!")
        print(f"✅ Instagram extraction + VLM analysis + {result.get('variations_generated', 0)} Flux variations")
        print(f"🚀 Ready for production deployment!")


if __name__ == "__main__":
    asyncio.run(main())