#!/usr/bin/env python3
"""
Instagram VLM Pipeline

Uses Instagram shortcodes to:
1. Get a sample post with shortcode
2. Fetch the actual Instagram image using the shortcode
3. Use VLM to extract description from the real Instagram image
4. Generate SiliconSentiments brand prompt
5. Generate new image with Flux
6. Save with complete metadata
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

class InstagramVLMPipeline:
    """Pipeline that fetches Instagram images using shortcodes and processes with VLM"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.replicate_token = replicate_token
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
    
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
    
    def get_sample_post_with_shortcode(self) -> Optional[Dict[str, Any]]:
        """Get a sample post that has a shortcode"""
        try:
            # Get a post with a shortcode (either with or without existing images)
            post = self.db.posts.find_one({
                "shortcode": {"$exists": True, "$ne": "", "$ne": None}
            })
            
            if not post:
                print("❌ No posts with shortcodes found")
                return None
            
            instagram_url = f"https://instagram.com/p/{post['shortcode']}"
            
            print(f"✅ Found post with shortcode: {post['shortcode']}")
            print(f"🔗 Instagram URL: {instagram_url}")
            
            return {
                "post_data": post,
                "shortcode": post["shortcode"],
                "caption": post.get("caption", ""),
                "instagram_url": instagram_url,
                "has_existing_image": "image_ref" in post
            }
            
        except Exception as e:
            print(f"❌ Error getting sample post: {e}")
            return None
    
    async def fetch_instagram_image_url(self, shortcode: str) -> Optional[str]:
        """Fetch the actual Instagram image URL using the shortcode"""
        try:
            print(f"📱 Fetching Instagram image for shortcode: {shortcode}")
            
            # Method 1: Try Instagram's public API endpoint
            instagram_url = f"https://www.instagram.com/p/{shortcode}/"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                try:
                    async with session.get(instagram_url, headers=headers) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            
                            # Look for image URL in the HTML
                            # Instagram embeds image URLs in various places
                            import re
                            
                            # Try to find the main image URL patterns
                            patterns = [
                                r'"display_url":"([^"]+)"',
                                r'"src":"([^"]+\.jpg[^"]*)"',
                                r'"url":"([^"]+\.jpg[^"]*)"',
                                r'content="([^"]+\.jpg[^"]*)" property="og:image"'
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, html_content)
                                if matches:
                                    # Clean up the URL (remove escape characters)
                                    image_url = matches[0].replace('\\u0026', '&').replace('\\/', '/')
                                    
                                    # Validate it looks like an image URL
                                    if any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                        print(f"   ✅ Found image URL: {image_url[:60]}...")
                                        return image_url
                        
                        print(f"   ⚠️  Could not extract image URL from HTML (status: {response.status})")
                        
                except Exception as e:
                    print(f"   ⚠️  Instagram fetch failed: {e}")
            
            # Method 2: Try alternative approach or return None
            print(f"   ❌ Could not fetch Instagram image for {shortcode}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Instagram image: {e}")
            return None
    
    async def extract_description_with_vlm(self, image_url: str, model: str = "blip") -> Dict[str, Any]:
        """Extract description from image using VLM"""
        try:
            import replicate
            
            print(f"🔍 Analyzing image with {model.upper()}...")
            print(f"   Image URL: {image_url[:60]}...")
            
            if model == "llava":
                # Use LLaVA for detailed artistic analysis
                output = replicate.run(
                    "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddda3e32fd8a0e75dc39d8a4191bb742157fb",
                    input={
                        "image": image_url,
                        "prompt": "Describe this Instagram image in detail. Focus on: 1) Visual composition and layout, 2) Color scheme and lighting effects, 3) Artistic style and technique, 4) Subject matter and themes, 5) Overall mood and aesthetic. Be specific and descriptive for creating similar digital artwork."
                    }
                )
            else:
                # Use BLIP for general image captioning
                output = replicate.run(
                    "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                    input={
                        "image": image_url,
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
                "source_url": image_url,
                "source_type": "instagram_image"
            }
            
        except Exception as e:
            print(f"   ❌ VLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_used": model,
                "timestamp": datetime.now(timezone.utc)
            }
    
    def fallback_caption_analysis(self, caption: str, shortcode: str) -> Dict[str, Any]:
        """Fallback: analyze caption if image fetch fails"""
        try:
            print(f"🔄 Using caption analysis as fallback...")
            print(f"   📝 Caption: {caption[:150]}...")
            
            # Analyze caption to create description
            if not caption or len(caption.strip()) < 10:
                description = f"Instagram post from @siliconsentiments_art (post {shortcode}): Digital artwork featuring modern technological themes with clean aesthetic design"
            else:
                # Extract key themes from caption
                tech_keywords = ["ai", "digital", "cyber", "tech", "future", "neural", "quantum", "algorithm", "data", "silicon"]
                art_keywords = ["art", "design", "visual", "aesthetic", "style", "creative", "generative", "artwork"]
                
                has_tech = any(keyword in caption.lower() for keyword in tech_keywords)
                has_art = any(keyword in caption.lower() for keyword in art_keywords)
                
                if has_tech and has_art:
                    base_desc = "Instagram post featuring advanced digital artwork combining technological elements with artistic design"
                elif has_tech:
                    base_desc = "Instagram post showcasing technology-focused digital composition with futuristic elements"
                elif has_art:
                    base_desc = "Instagram post displaying artistic digital creation with modern aesthetic elements"
                else:
                    base_desc = "Instagram post showing contemporary digital artwork with clean modern styling"
                
                description = f"{base_desc}. Caption context: {caption[:150]}"
            
            print(f"   ✅ Caption-based description generated")
            print(f"   📝 Description: {description[:200]}...")
            
            return {
                "success": True,
                "description": description,
                "model_used": "caption_analysis_fallback",
                "timestamp": datetime.now(timezone.utc),
                "source_caption": caption,
                "source_type": "caption_fallback"
            }
            
        except Exception as e:
            print(f"   ❌ Caption analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_used": "caption_analysis_fallback",
                "timestamp": datetime.now(timezone.utc)
            }
    
    def generate_siliconsentiments_prompt(self, description: str, style: str = "advanced") -> str:
        """Generate SiliconSentiments brand prompt"""
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
            prompt = f"SiliconSentiments {theme} inspired by: {description[:100]}, {visual}, {colors}, clean composition, Instagram-ready"
            
        elif style == "advanced":
            visuals = random.sample(visual_elements, 3)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"SiliconSentiments {theme} inspired by: {description[:120]}, {', '.join(visuals)}, {colors}, {quality}, atmospheric lighting, Instagram-ready composition"
            
        elif style == "experimental":
            visuals = random.sample(visual_elements, 4)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"Advanced SiliconSentiments {theme} reimagining: {description[:100]}, incorporating {', '.join(visuals)}, {colors}, {quality}, award-winning digital art"
        
        print(f"🎨 Generated {style} SiliconSentiments prompt:")
        print(f"   📝 {prompt[:100]}...")
        
        return prompt
    
    async def generate_with_flux(self, prompt: str, model: str = "flux-schnell") -> Dict[str, Any]:
        """Generate image using Flux"""
        try:
            import replicate
            
            print(f"🖼️  Generating image with {model}...")
            
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
                "generation_params": config["params"]
            }
            
        except Exception as e:
            print(f"   ❌ Flux generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "prompt": prompt
            }
    
    async def save_original_instagram_image(self, image_url: str, shortcode: str) -> Optional[str]:
        """Download and save original Instagram image for comparison"""
        try:
            print(f"📥 Downloading original Instagram image...")
            
            # Create comparison directory
            comparison_dir = "instagram_vlm_comparison"
            os.makedirs(comparison_dir, exist_ok=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Save original image locally
                        original_filename = f"{shortcode}_original_instagram.jpg"
                        original_path = os.path.join(comparison_dir, original_filename)
                        
                        with open(original_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"   ✅ Original saved: {original_path}")
                        print(f"   📏 Original size: {len(image_data)} bytes")
                        
                        return os.path.abspath(original_path)
                    else:
                        print(f"   ❌ Original download failed: HTTP {response.status}")
                        return None
            
        except Exception as e:
            print(f"   ❌ Original save failed: {e}")
            return None
    
    async def download_and_save_image(self, image_url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Download generated image and save to GridFS"""
        try:
            print(f"📥 Downloading and saving image...")
            
            # Create comparison directory
            comparison_dir = "instagram_vlm_comparison"
            os.makedirs(comparison_dir, exist_ok=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Save generated image locally for comparison
                        shortcode = metadata.get('shortcode', 'unknown')
                        generated_filename = f"{shortcode}_generated_flux.png"
                        generated_path = os.path.join(comparison_dir, generated_filename)
                        
                        with open(generated_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"   ✅ Generated image saved locally: {generated_path}")
                        
                        # Also save to GridFS
                        filename = f"instagram_vlm_flux_{shortcode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        
                        file_id = self.fs.put(
                            image_data,
                            filename=filename,
                            contentType="image/png",
                            metadata={
                                "brand": "siliconsentiments",
                                "automated": True,
                                "generator_version": "instagram_vlm_flux_v1.0",
                                "pipeline": "instagram_vlm_to_flux",
                                "generated_at": datetime.now(timezone.utc),
                                "source_platform": "instagram",
                                "shortcode": metadata.get("shortcode"),
                                "instagram_url": metadata.get("instagram_url"),
                                "vlm_model": metadata.get("vlm_model", "unknown"),
                                "generation_model": metadata.get("generation_model", "unknown"),
                                "description_source": metadata.get("description_source", "unknown"),
                                "original_description": metadata.get("original_description", ""),
                                "brand_prompt": metadata.get("brand_prompt", ""),
                                "cost": metadata.get("cost", 0),
                                **metadata
                            }
                        )
                        
                        print(f"   ✅ Saved to GridFS: {file_id}")
                        print(f"   📏 File size: {len(image_data)} bytes")
                        
                        return str(file_id)
                    else:
                        print(f"   ❌ Download failed: HTTP {response.status}")
                        return None
            
        except Exception as e:
            print(f"   ❌ Download/save failed: {e}")
            return None
    
    async def run_instagram_vlm_pipeline(
        self, 
        vlm_model: str = "blip",
        flux_model: str = "flux-schnell",
        prompt_style: str = "advanced"
    ) -> Dict[str, Any]:
        """Run the complete Instagram VLM to Flux pipeline"""
        
        print("🚀 INSTAGRAM VLM TO FLUX PIPELINE")
        print("=" * 60)
        print(f"📱 Source: Instagram (via shortcode)")
        print(f"🔍 VLM Model: {vlm_model}")
        print(f"🖼️  Flux Model: {flux_model}")
        print(f"🎨 Prompt Style: {prompt_style}")
        print("=" * 60)
        
        if not self.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # Step 1: Get sample post with shortcode
            print("1️⃣ GETTING SAMPLE POST WITH SHORTCODE...")
            sample_data = self.get_sample_post_with_shortcode()
            if not sample_data:
                return {"success": False, "error": "No suitable sample post found"}
            
            shortcode = sample_data["shortcode"]
            caption = sample_data["caption"]
            instagram_url = sample_data["instagram_url"]
            
            # Step 2: Try to fetch Instagram image
            print("\n2️⃣ FETCHING INSTAGRAM IMAGE...")
            instagram_image_url = await self.fetch_instagram_image_url(shortcode)
            
            # Save original Instagram image if found
            original_image_path = None
            if instagram_image_url:
                original_image_path = await self.save_original_instagram_image(instagram_image_url, shortcode)
            
            # Step 3: Extract description (VLM or fallback)
            print("\n3️⃣ EXTRACTING DESCRIPTION...")
            
            if instagram_image_url:
                print("   🖼️  Using real Instagram image with VLM")
                description_result = await self.extract_description_with_vlm(instagram_image_url, vlm_model)
                source_image_url = instagram_image_url
            else:
                print("   📝 Using caption analysis as fallback")
                description_result = self.fallback_caption_analysis(caption, shortcode)
                source_image_url = None
            
            if not description_result["success"]:
                return {"success": False, "error": f"Description extraction failed: {description_result['error']}"}
            
            # Step 4: Generate SiliconSentiments prompt
            print("\n4️⃣ GENERATING SILICONSENTIMENTS PROMPT...")
            brand_prompt = self.generate_siliconsentiments_prompt(description_result["description"], prompt_style)
            
            # Step 5: Generate with Flux
            print("\n5️⃣ GENERATING WITH FLUX...")
            flux_result = await self.generate_with_flux(brand_prompt, flux_model)
            if not flux_result["success"]:
                return {"success": False, "error": f"Flux generation failed: {flux_result['error']}"}
            
            # Step 6: Download and save
            print("\n6️⃣ DOWNLOADING AND SAVING...")
            
            pipeline_data = {
                "shortcode": shortcode,
                "instagram_url": instagram_url,
                "vlm_model": description_result["model_used"],
                "generation_model": flux_model,
                "original_description": description_result["description"],
                "brand_prompt": brand_prompt,
                "image_url": flux_result["image_url"],
                "cost": flux_result["cost"],
                "source_image_url": source_image_url,
                "description_source": description_result["source_type"],
                "description_timestamp": description_result["timestamp"],
                "prompt_style": prompt_style,
                "generation_params": flux_result.get("generation_params", {})
            }
            
            file_id = await self.download_and_save_image(flux_result["image_url"], pipeline_data)
            if not file_id:
                return {"success": False, "error": "Failed to download/save image"}
            
            print("\n🎉 INSTAGRAM VLM PIPELINE COMPLETE!")
            print("=" * 60)
            print(f"✅ Successfully processed Instagram post")
            print(f"📱 Instagram: {instagram_url}")
            print(f"🔍 Description method: {description_result['model_used']}")
            print(f"📝 Description: {description_result['description'][:100]}...")
            print(f"🎨 Brand prompt: {brand_prompt[:100]}...")
            print(f"🖼️  New image: {flux_result['image_url'][:60]}...")
            print(f"💰 Cost: ${flux_result['cost']:.4f}")
            print(f"💾 Saved to GridFS: {file_id}")
            
            # Show comparison files
            comparison_dir = os.path.abspath("instagram_vlm_comparison")
            print(f"\n📂 COMPARISON FILES:")
            print(f"   Folder: {comparison_dir}")
            
            if source_image_url and original_image_path:
                print(f"   📸 Original: {shortcode}_original_instagram.jpg")
                print(f"   🖼️  Generated: {shortcode}_generated_flux.png")
                print(f"   🔍 Source: Real Instagram image analyzed with {vlm_model}")
            else:
                print(f"   🖼️  Generated: {shortcode}_generated_flux.png")
                print(f"   📝 Source: Caption analysis (image fetch failed)")
            
            print(f"\n💡 Open the comparison folder to view original vs generated images!")
            
            return {
                "success": True,
                "shortcode": shortcode,
                "instagram_url": instagram_url,
                "description_method": description_result["model_used"],
                "original_description": description_result["description"],
                "brand_prompt": brand_prompt,
                "new_image_url": flux_result["image_url"],
                "file_id": file_id,
                "cost": flux_result["cost"],
                "source_image_available": source_image_url is not None,
                "source_image_url": source_image_url
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            if self.client:
                self.client.close()

async def main():
    """Run the Instagram VLM pipeline demo"""
    
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    pipeline = InstagramVLMPipeline(replicate_token)
    
    # Try with BLIP first (simpler/faster)
    result = await pipeline.run_instagram_vlm_pipeline(
        vlm_model="blip",
        flux_model="flux-schnell",
        prompt_style="advanced"
    )
    
    if result["success"]:
        print(f"\n🎊 PIPELINE SUCCESS!")
        print(f"   Instagram Post: {result['shortcode']}")
        print(f"   URL: {result['instagram_url']}")
        print(f"   Description Method: {result['description_method']}")
        print(f"   New Image: {result['new_image_url']}")
        print(f"   Cost: ${result['cost']:.4f}")
        
        if result["source_image_available"]:
            print(f"   ✅ Used real Instagram image with VLM analysis")
        else:
            print(f"   📝 Used caption analysis (image not accessible)")
            
        print(f"\n💡 This demonstrates the complete Instagram → VLM → Flux workflow!")
    else:
        print(f"❌ Pipeline failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())