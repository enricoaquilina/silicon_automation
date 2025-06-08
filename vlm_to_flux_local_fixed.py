#!/usr/bin/env python3
"""
VLM to Flux Pipeline - Local Images Version (Fixed)
Process the 5 verified Instagram images from downloaded_verify_images/
"""

import os
import asyncio
import aiohttp
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from gridfs import GridFS
from PIL import Image
import hashlib

class VLMToFluxLocalPipeline:
    """VLM-to-Flux pipeline for local filesystem images"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.replicate_token = replicate_token
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
        self.base_dir = "downloaded_verify_images"
    
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def scan_local_images(self) -> List[Dict[str, Any]]:
        """Scan downloaded_verify_images for available images"""
        if not os.path.exists(self.base_dir):
            print(f"❌ Directory {self.base_dir} not found")
            return []
        
        image_data = []
        
        # Get all subdirectories (one per shortcode)
        subdirs = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        
        for subdir in subdirs:
            shortcode = subdir.replace('verify_', '')
            subdir_path = os.path.join(self.base_dir, subdir)
            
            # Find image files
            image_files = [f for f in os.listdir(subdir_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            
            if not image_files:
                continue
            
            # Get the first (main) image
            main_image = image_files[0]
            image_path = os.path.join(subdir_path, main_image)
            
            # Get image info
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_type = img.format
                
                file_size = os.path.getsize(image_path)
                
                image_data.append({
                    'shortcode': shortcode,
                    'image_path': image_path,
                    'filename': main_image,
                    'size': f'{width}x{height}',
                    'file_size': file_size,
                    'format': format_type,
                    'instagram_url': f'https://instagram.com/p/{shortcode}/'
                })
                
            except Exception as e:
                print(f"⚠️  Error reading {image_path}: {e}")
        
        return image_data
    
    async def extract_description_with_vlm(self, image_path: str, shortcode: str, model: str = "blip") -> Dict[str, Any]:
        """Extract description from local image using VLM"""
        try:
            import replicate
            
            print(f"🔍 Analyzing {shortcode} with {model.upper()}...")
            print(f"   Local path: {image_path}")
            
            # Open and process the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create a data URI for the image
            import base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine the MIME type
            if image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif image_path.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/jpeg'  # default
            
            data_uri = f"data:{mime_type};base64,{encoded_image}"
            
            if model == "llava":
                # Use LLaVA for detailed artistic analysis
                output = replicate.run(
                    "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddda3e32fd8a0e75dc39d8a4191bb742157fb",
                    input={
                        "image": data_uri,
                        "prompt": "Describe this digital artwork in detail. Focus on: 1) Visual composition and layout, 2) Color scheme and lighting effects, 3) Artistic style and technique, 4) Subject matter and themes, 5) Overall mood and aesthetic. Be specific and descriptive for creating similar artwork."
                    }
                )
            else:
                # Use BLIP for general image captioning
                output = replicate.run(
                    "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                    input={
                        "image": data_uri,
                        "task": "image_captioning"
                    }
                )
            
            description = output if isinstance(output, str) else str(output)
            
            print(f"   ✅ Description extracted ({len(description)} chars)")
            print(f"   📝 Description: {description[:200]}...")
            
            return {
                "success": True,
                "description": description,
                "model_used": model,
                "timestamp": datetime.now(timezone.utc),
                "source_path": image_path,
                "shortcode": shortcode
            }
            
        except Exception as e:
            print(f"   ❌ VLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_used": model,
                "timestamp": datetime.now(timezone.utc),
                "shortcode": shortcode
            }
    
    def generate_siliconsentiments_prompt(self, description: str, shortcode: str, style: str = "advanced") -> str:
        """Generate SiliconSentiments brand prompt from VLM description"""
        import random
        
        # Core SiliconSentiments themes
        tech_themes = [
            "neural network consciousness visualization",
            "quantum computing interface design",
            "cybernetic organism architecture", 
            "artificial intelligence emergence patterns",
            "blockchain reality matrix systems",
            "algorithmic pattern recognition art",
            "digital consciousness evolution process",
            "holographic data visualization networks"
        ]
        
        # Visual enhancement elements
        visual_elements = [
            "clean geometric minimalism",
            "precision-engineered surfaces",
            "neon-lit circuit aesthetics",
            "crystalline structure formations",
            "liquid metal transformations",
            "wireframe architectural blueprints",
            "holographic transparency effects",
            "gradient color transitions",
            "ambient atmospheric lighting",
            "particle system dynamics"
        ]
        
        # Color schemes 
        color_palettes = [
            "electric blue and cyan harmonies",
            "deep purple and magenta gradients",
            "emerald green circuit patterns", 
            "golden amber accent highlights",
            "chrome and silver metallics",
            "prismatic rainbow refractions",
            "monochromatic depth studies"
        ]
        
        # Quality modifiers
        quality_specs = [
            "8K ultra-resolution clarity",
            "photorealistic rendering quality",
            "volumetric lighting effects",
            "sharp geometric precision",
            "professional studio composition",
            "cinematic color grading"
        ]
        
        # Build prompt based on style
        theme = random.choice(tech_themes)
        
        if style == "simple":
            visual = random.choice(visual_elements[:3])
            colors = random.choice(color_palettes)
            prompt = f"SiliconSentiments {theme} inspired by Instagram post {shortcode}: {description[:100]}, {visual}, {colors}, clean composition, Instagram-ready"
            
        elif style == "advanced":
            visuals = random.sample(visual_elements, 3)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"SiliconSentiments {theme} reimagining Instagram {shortcode}: {description[:150]}, {', '.join(visuals)}, {colors}, {quality}, atmospheric lighting, Instagram-ready composition"
            
        elif style == "experimental":
            visuals = random.sample(visual_elements, 4)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"Advanced SiliconSentiments {theme} transformation of {shortcode}: {description[:120]}, incorporating {', '.join(visuals)}, {colors}, {quality}, award-winning digital art, cutting-edge technology aesthetic"
        
        print(f"🎨 Generated {style} SiliconSentiments prompt:")
        print(f"   📝 {prompt[:150]}...")
        
        return prompt
    
    async def generate_with_flux(self, prompt: str, shortcode: str, model: str = "flux-schnell") -> Dict[str, Any]:
        """Generate image using Flux"""
        try:
            import replicate
            
            print(f"🖼️  Generating image for {shortcode} with {model}...")
            print(f"   🎯 Prompt: {prompt[:80]}...")
            
            # Model configurations
            model_configs = {
                "flux-schnell": {
                    "model": "black-forest-labs/flux-schnell",
                    "cost": 0.003,
                    "params": {"num_inference_steps": 4}
                },
                "flux-dev": {
                    "model": "black-forest-labs/flux-dev",
                    "cost": 0.055,
                    "params": {"num_inference_steps": 50}
                }
            }
            
            config = model_configs.get(model, model_configs["flux-schnell"])
            
            # Generate image
            output = replicate.run(
                config["model"],
                input={
                    "prompt": prompt,
                    "num_outputs": 1,
                    "width": 1024,
                    "height": 1024,
                    **config["params"]
                }
            )
            
            image_url = str(output[0]) if isinstance(output, list) else str(output)
            
            print(f"   ✅ Image generated!")
            print(f"   🔗 URL: {image_url[:60]}...")
            
            return {
                "success": True,
                "image_url": image_url,
                "model": model,
                "cost": config["cost"],
                "prompt": prompt,
                "generation_params": config["params"],
                "shortcode": shortcode
            }
            
        except Exception as e:
            print(f"   ❌ Flux generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "prompt": prompt,
                "shortcode": shortcode
            }
    
    async def download_and_save_image(self, image_url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Download generated image and save to GridFS"""
        try:
            print(f"📥 Downloading and saving image for {metadata.get('shortcode')}...")
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Save to GridFS
                        shortcode = metadata.get('shortcode', 'unknown')
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"vlm_flux_local_{shortcode}_{timestamp}.png"
                        
                        file_id = self.fs.put(
                            image_data,
                            filename=filename,
                            contentType="image/png",
                            metadata={
                                "brand": "siliconsentiments",
                                "automated": True,
                                "generator_version": "vlm_flux_local_v1.0",
                                "pipeline": "vlm_to_flux_local",
                                "generated_at": datetime.now(timezone.utc),
                                "vlm_model": metadata.get("vlm_model", "unknown"),
                                "generation_model": metadata.get("generation_model", "unknown"),
                                "original_description": metadata.get("original_description", ""),
                                "brand_prompt": metadata.get("brand_prompt", ""),
                                "cost": metadata.get("cost", 0),
                                "source_type": "local_instagram_original",
                                "original_image_path": metadata.get("original_image_path", ""),
                                **metadata
                            }
                        )
                        
                        print(f"   ✅ Saved to GridFS: {file_id}")
                        print(f"   📏 File size: {len(image_data)} bytes")
                        
                        # Also save locally for immediate viewing
                        local_output_dir = "vlm_flux_results"
                        os.makedirs(local_output_dir, exist_ok=True)
                        local_path = os.path.join(local_output_dir, filename)
                        
                        with open(local_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"   💾 Also saved locally: {local_path}")
                        
                        return str(file_id)
                    else:
                        print(f"   ❌ Download failed: HTTP {response.status}")
                        return None
            
        except Exception as e:
            print(f"   ❌ Download/save failed: {e}")
            return None
    
    async def process_single_image(
        self, 
        image_info: Dict[str, Any],
        vlm_model: str = "blip",
        flux_model: str = "flux-schnell", 
        prompt_style: str = "advanced"
    ) -> Dict[str, Any]:
        """Process a single image through the VLM-to-Flux pipeline"""
        
        shortcode = image_info['shortcode']
        image_path = image_info['image_path']
        
        print(f"\n🚀 PROCESSING {shortcode}")
        print(f"=" * 60)
        print(f"📸 Source: {image_path}")
        print(f"🔍 VLM Model: {vlm_model}")
        print(f"🎨 Flux Model: {flux_model}")
        print(f"✨ Style: {prompt_style}")
        
        try:
            # Step 1: VLM Analysis
            print(f"\n1️⃣ VLM ANALYSIS...")
            vlm_result = await self.extract_description_with_vlm(image_path, shortcode, vlm_model)
            if not vlm_result["success"]:
                return {"success": False, "error": f"VLM analysis failed: {vlm_result['error']}", "shortcode": shortcode}
            
            # Step 2: Generate SiliconSentiments prompt
            print(f"\n2️⃣ GENERATING SILICONSENTIMENTS PROMPT...")
            brand_prompt = self.generate_siliconsentiments_prompt(vlm_result["description"], shortcode, prompt_style)
            
            # Step 3: Generate with Flux
            print(f"\n3️⃣ GENERATING WITH FLUX...")
            flux_result = await self.generate_with_flux(brand_prompt, shortcode, flux_model)
            if not flux_result["success"]:
                return {"success": False, "error": f"Flux generation failed: {flux_result['error']}", "shortcode": shortcode}
            
            # Step 4: Download and save
            print(f"\n4️⃣ DOWNLOADING AND SAVING...")
            pipeline_data = {
                "shortcode": shortcode,
                "vlm_model": vlm_model,
                "generation_model": flux_model,
                "original_description": vlm_result["description"],
                "brand_prompt": brand_prompt,
                "image_url": flux_result["image_url"],
                "cost": flux_result["cost"],
                "original_image_path": image_path,
                "vlm_timestamp": vlm_result["timestamp"],
                "prompt_style": prompt_style,
                "generation_params": flux_result.get("generation_params", {}),
                "source_image_info": image_info
            }
            
            file_id = await self.download_and_save_image(flux_result["image_url"], pipeline_data)
            if not file_id:
                return {"success": False, "error": "Failed to download/save image", "shortcode": shortcode}
            
            # Success!
            print(f"\n✅ SUCCESS FOR {shortcode}!")
            print(f"💰 Cost: ${flux_result['cost']:.4f}")
            print(f"💾 GridFS ID: {file_id}")
            print(f"🔗 Original Instagram: {image_info['instagram_url']}")
            
            return {
                "success": True,
                "shortcode": shortcode,
                "instagram_url": image_info['instagram_url'],
                "vlm_description": vlm_result["description"],
                "brand_prompt": brand_prompt,
                "new_image_url": flux_result["image_url"],
                "file_id": file_id,
                "cost": flux_result["cost"],
                "models_used": {
                    "vlm": vlm_model,
                    "generation": flux_model
                },
                "source_image_info": image_info
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed for {shortcode}: {e}")
            return {"success": False, "error": str(e), "shortcode": shortcode}
    
    async def run_batch_processing(
        self,
        vlm_model: str = "blip",
        flux_model: str = "flux-schnell",
        prompt_style: str = "advanced"
    ) -> Dict[str, Any]:
        """Run VLM-to-Flux pipeline on all local images"""
        
        print("🚀 VLM TO FLUX PIPELINE - LOCAL IMAGES (FIXED)")
        print("=" * 60)
        print(f"🔍 VLM Model: {vlm_model}")
        print(f"🖼️  Flux Model: {flux_model}")
        print(f"🎨 Prompt Style: {prompt_style}")
        print("=" * 60)
        
        # Connect to database
        if not self.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        # Scan for local images
        print(f"\n📁 SCANNING LOCAL IMAGES...")
        image_data = self.scan_local_images()
        
        if not image_data:
            return {"success": False, "error": "No local images found"}
        
        print(f"Found {len(image_data)} local Instagram images:")
        for img in image_data:
            print(f"  📸 {img['shortcode']}: {img['filename']} ({img['size']})")
        
        # Process each image
        results = []
        total_cost = 0
        
        for i, image_info in enumerate(image_data, 1):
            print(f"\n🔄 PROCESSING {i}/{len(image_data)}")
            
            result = await self.process_single_image(
                image_info, 
                vlm_model=vlm_model,
                flux_model=flux_model,
                prompt_style=prompt_style
            )
            
            results.append(result)
            
            if result["success"]:
                total_cost += result["cost"]
                print(f"✅ {result['shortcode']} completed successfully!")
            else:
                print(f"❌ {result['shortcode']} failed: {result['error']}")
            
            # Small delay between generations
            if i < len(image_data):
                print(f"⏳ Waiting 5 seconds before next generation...")
                await asyncio.sleep(5)
        
        # Summary
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n🎉 BATCH PROCESSING COMPLETE!")
        print(f"=" * 60)
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"💰 Total cost: ${total_cost:.4f}")
        
        if successful:
            print(f"\n🎯 SUCCESSFUL GENERATIONS:")
            for result in successful:
                print(f"  ✅ {result['shortcode']}: ${result['cost']:.4f}")
                print(f"     VLM: {result['vlm_description'][:100]}...")
                print(f"     Prompt: {result['brand_prompt'][:100]}...")
        
        if failed:
            print(f"\n❌ FAILED GENERATIONS:")
            for result in failed:
                print(f"  ❌ {result['shortcode']}: {result['error']}")
        
        # Save results
        results_filename = f"vlm_flux_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_filename, 'w') as f:
            json.dump({
                "summary": {
                    "total_processed": len(image_data),
                    "successful": len(successful),
                    "failed": len(failed),
                    "total_cost": total_cost,
                    "models_used": {"vlm": vlm_model, "flux": flux_model},
                    "prompt_style": prompt_style,
                    "timestamp": datetime.now().isoformat()
                },
                "results": results
            }, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {results_filename}")
        
        if self.client:
            self.client.close()
        
        return {
            "success": True,
            "total_processed": len(image_data),
            "successful": len(successful),
            "failed": len(failed),
            "total_cost": total_cost,
            "results": results
        }

async def main():
    """Run the VLM to Flux pipeline on local images"""
    
    # Get API token
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize pipeline
    pipeline = VLMToFluxLocalPipeline(replicate_token)
    
    # Run pipeline
    result = await pipeline.run_batch_processing(
        vlm_model="blip",  # Start with BLIP for speed
        flux_model="flux-schnell",  # Low cost for testing
        prompt_style="advanced"  # Good balance of quality and complexity
    )
    
    if result["success"]:
        print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"Generated {result['successful']} SiliconSentiments images")
        print(f"Total cost: ${result['total_cost']:.4f}")
    else:
        print(f"\n❌ Pipeline failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())