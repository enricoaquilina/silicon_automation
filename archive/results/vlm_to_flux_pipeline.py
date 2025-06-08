#!/usr/bin/env python3
"""
VLM to Flux Pipeline

A streamlined pipeline that:
1. Gets a sample Instagram post 
2. Uses VLM to extract description from existing image
3. Generates SiliconSentiments brand prompt
4. Generates new image with Flux
5. Saves with complete metadata
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

class VLMToFluxPipeline:
    """Complete pipeline from VLM analysis to Flux generation"""
    
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
    
    def get_sample_post_with_image(self) -> Optional[Dict[str, Any]]:
        """Get a sample post that already has an image"""
        try:
            # Get a post that has an existing image but could use regeneration
            post = self.db.posts.find_one({
                "image_ref": {"$exists": True},
                "shortcode": {"$exists": True}
            })
            
            if not post:
                print("❌ No posts with images found")
                return None
            
            # Get the image data
            image_doc = self.db.post_images.find_one({"_id": post["image_ref"]})
            if not image_doc:
                print("❌ Image document not found")
                return None
            
            # Extract image URL from the generation data
            image_url = None
            if "images" in image_doc and image_doc["images"]:
                for image in image_doc["images"]:
                    if "midjourney_generations" in image:
                        for gen in image["midjourney_generations"]:
                            if gen.get("image_url"):
                                image_url = gen["image_url"]
                                break
                        if image_url:
                            break
            
            if not image_url:
                print("❌ No image URL found in existing generation")
                return None
            
            return {
                "post_data": post,
                "image_doc": image_doc,
                "image_url": image_url,
                "shortcode": post.get("shortcode", "unknown"),
                "caption": post.get("caption", ""),
                "instagram_url": f"https://instagram.com/p/{post.get('shortcode', '')}"
            }
            
        except Exception as e:
            print(f"❌ Error getting sample post: {e}")
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
                        "prompt": "Describe this digital artwork in detail. Focus on: 1) Visual composition and layout, 2) Color scheme and lighting effects, 3) Artistic style and technique, 4) Subject matter and themes, 5) Overall mood and aesthetic. Be specific and descriptive for creating similar artwork."
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
                "source_url": image_url
            }
            
        except Exception as e:
            print(f"   ❌ VLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_used": model,
                "timestamp": datetime.now(timezone.utc)
            }
    
    def generate_siliconsentiments_prompt(self, description: str, style: str = "advanced") -> str:
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
            # Simple style for fast generation
            visual = random.choice(visual_elements[:3])  # Use simpler elements
            colors = random.choice(color_palettes)
            prompt = f"SiliconSentiments {theme} inspired by: {description[:100]}, {visual}, {colors}, clean composition, Instagram-ready"
            
        elif style == "advanced":
            # Advanced style with more elements
            visuals = random.sample(visual_elements, 3)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"SiliconSentiments {theme} inspired by: {description[:150]}, {', '.join(visuals)}, {colors}, {quality}, atmospheric lighting, Instagram-ready composition"
            
        elif style == "experimental":
            # Experimental style with maximum elements
            visuals = random.sample(visual_elements, 4)
            colors = random.choice(color_palettes)
            quality = random.choice(quality_specs)
            prompt = f"Advanced SiliconSentiments {theme} reimagining: {description[:120]}, incorporating {', '.join(visuals)}, {colors}, {quality}, award-winning digital art, cutting-edge technology aesthetic"
        
        print(f"🎨 Generated {style} SiliconSentiments prompt:")
        print(f"   📝 {prompt[:100]}...")
        
        return prompt
    
    async def generate_with_flux(self, prompt: str, model: str = "flux-schnell") -> Dict[str, Any]:
        """Generate image using Flux"""
        try:
            import replicate
            
            print(f"🖼️  Generating image with {model}...")
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
    
    async def download_and_save_image(self, image_url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Download generated image and save to GridFS"""
        try:
            print(f"📥 Downloading and saving image...")
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Save to GridFS
                        filename = f"vlm_flux_{metadata.get('shortcode', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        
                        file_id = self.fs.put(
                            image_data,
                            filename=filename,
                            contentType="image/png",
                            metadata={
                                "brand": "siliconsentiments",
                                "automated": True,
                                "generator_version": "vlm_flux_v1.0",
                                "pipeline": "vlm_to_flux",
                                "generated_at": datetime.now(timezone.utc),
                                "vlm_model": metadata.get("vlm_model", "unknown"),
                                "generation_model": metadata.get("generation_model", "unknown"),
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
    
    def create_generation_document(self, post_id: str, file_id: str, pipeline_data: Dict[str, Any]) -> Optional[str]:
        """Create post_images document with VLM pipeline data"""
        try:
            print(f"📄 Creating generation document...")
            
            # Create comprehensive generation document
            post_images_doc = {
                "post_id": post_id,
                "images": [{
                    "midjourney_generations": [{
                        "variation": f"vlm_flux_{pipeline_data['generation_model']}_v1.0",
                        "prompt": pipeline_data["brand_prompt"],
                        "timestamp": datetime.now(timezone.utc),
                        "message_id": f"vlm_flux_auto_{post_id}",
                        "grid_message_id": f"vlm_flux_grid_{post_id}",
                        "variant_idx": 1,
                        "options": {
                            "automated": True,
                            "provider": "replicate",
                            "model": pipeline_data["generation_model"],
                            "pipeline": "vlm_to_flux",
                            "vlm_model": pipeline_data["vlm_model"],
                            "original_description": pipeline_data["vlm_description"],
                            "brand_adaptation": "siliconsentiments_vlm_v1.0",
                            "generation_params": pipeline_data.get("generation_params", {}),
                            "style": pipeline_data.get("prompt_style", "advanced")
                        },
                        "file_id": file_id,
                        "midjourney_image_id": file_id,
                        "image_url": pipeline_data["image_url"],
                        
                        # VLM-specific metadata
                        "vlm_analysis": {
                            "model": pipeline_data["vlm_model"],
                            "description": pipeline_data["vlm_description"],
                            "analyzed_at": pipeline_data["vlm_timestamp"],
                            "source_image_url": pipeline_data["source_image_url"]
                        },
                        
                        # Generation metadata
                        "generation_metadata": {
                            "cost": pipeline_data["cost"],
                            "model": pipeline_data["generation_model"],
                            "pipeline_version": "1.0",
                            "quality_score": None,  # To be filled later
                            "brand_consistency_score": None  # To be filled later
                        }
                    }]
                }],
                "created_at": datetime.now(timezone.utc),
                "status": "generated_vlm_flux",
                
                # Enhanced automation info
                "automation_info": {
                    "generated_by": "vlm_to_flux_pipeline_v1.0",
                    "cost": pipeline_data["cost"],
                    "provider": "replicate",
                    "model": pipeline_data["generation_model"],
                    "vlm_model": pipeline_data["vlm_model"],
                    "pipeline_type": "vlm_analysis_to_generation",
                    "description_source": "vlm_extracted",
                    "generation_timestamp": datetime.now(timezone.utc),
                    "session_id": f"vlm_flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                },
                
                # VLM pipeline specific data
                "vlm_pipeline_data": {
                    "source_image_url": pipeline_data["source_image_url"],
                    "vlm_description": pipeline_data["vlm_description"],
                    "brand_prompt": pipeline_data["brand_prompt"],
                    "prompt_style": pipeline_data.get("prompt_style", "advanced"),
                    "pipeline_version": "1.0"
                }
            }
            
            # Insert document
            result = self.db.post_images.insert_one(post_images_doc)
            image_ref_id = result.inserted_id
            
            print(f"   ✅ Generation document created: {image_ref_id}")
            
            return image_ref_id
            
        except Exception as e:
            print(f"   ❌ Document creation failed: {e}")
            return None
    
    def update_post_with_vlm_generation(self, post_id: str, image_ref_id: str, pipeline_data: Dict[str, Any]) -> bool:
        """Update post with VLM generation data"""
        try:
            print(f"📝 Updating post with VLM generation...")
            
            update_result = self.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "image_ref": image_ref_id,
                        "instagram_status": "ready_to_publish",
                        "automation_data": {
                            "generated_at": datetime.now(timezone.utc),
                            "provider": "replicate",
                            "model": pipeline_data["generation_model"],
                            "cost": pipeline_data["cost"],
                            "prompt": pipeline_data["brand_prompt"],
                            "automated": True,
                            "pipeline": "vlm_to_flux",
                            "vlm_model": pipeline_data["vlm_model"],
                            "version": "1.0"
                        },
                        "updated_at": datetime.now(timezone.utc),
                        
                        # VLM analysis data
                        "vlm_analysis": {
                            "description": pipeline_data["vlm_description"],
                            "model": pipeline_data["vlm_model"],
                            "analyzed_at": pipeline_data["vlm_timestamp"],
                            "source_image": pipeline_data["source_image_url"]
                        }
                    }
                }
            )
            
            success = update_result.modified_count > 0
            if success:
                print(f"   ✅ Post updated successfully")
            else:
                print(f"   ⚠️  Post update returned 0 modifications")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Post update failed: {e}")
            return False
    
    async def run_complete_pipeline(
        self, 
        vlm_model: str = "blip", 
        flux_model: str = "flux-schnell",
        prompt_style: str = "advanced"
    ) -> Dict[str, Any]:
        """Run the complete VLM to Flux pipeline"""
        
        print("🚀 VLM TO FLUX PIPELINE")
        print("=" * 60)
        print(f"🔍 VLM Model: {vlm_model}")
        print(f"🖼️  Flux Model: {flux_model}")
        print(f"🎨 Prompt Style: {prompt_style}")
        print("=" * 60)
        
        # Connect to database
        if not self.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # Step 1: Get sample post
            print("1️⃣ GETTING SAMPLE POST...")
            sample_data = self.get_sample_post_with_image()
            if not sample_data:
                return {"success": False, "error": "No suitable sample post found"}
            
            print(f"   ✅ Sample post: {sample_data['shortcode']}")
            print(f"   📸 Existing image: {sample_data['image_url'][:60]}...")
            print(f"   🔗 Instagram: {sample_data['instagram_url']}")
            
            # Step 2: Extract description with VLM
            print("\n2️⃣ EXTRACTING DESCRIPTION WITH VLM...")
            vlm_result = await self.extract_description_with_vlm(sample_data['image_url'], vlm_model)
            if not vlm_result["success"]:
                return {"success": False, "error": f"VLM analysis failed: {vlm_result['error']}"}
            
            # Step 3: Generate SiliconSentiments prompt
            print("\n3️⃣ GENERATING SILICONSENTIMENTS PROMPT...")
            brand_prompt = self.generate_siliconsentiments_prompt(vlm_result["description"], prompt_style)
            
            # Step 4: Generate with Flux
            print("\n4️⃣ GENERATING WITH FLUX...")
            flux_result = await self.generate_with_flux(brand_prompt, flux_model)
            if not flux_result["success"]:
                return {"success": False, "error": f"Flux generation failed: {flux_result['error']}"}
            
            # Step 5: Download and save image
            print("\n5️⃣ DOWNLOADING AND SAVING...")
            pipeline_data = {
                "shortcode": sample_data["shortcode"],
                "vlm_model": vlm_model,
                "generation_model": flux_model,
                "vlm_description": vlm_result["description"],
                "brand_prompt": brand_prompt,
                "image_url": flux_result["image_url"],
                "cost": flux_result["cost"],
                "source_image_url": sample_data["image_url"],
                "vlm_timestamp": vlm_result["timestamp"],
                "prompt_style": prompt_style,
                "generation_params": flux_result.get("generation_params", {})
            }
            
            file_id = await self.download_and_save_image(flux_result["image_url"], pipeline_data)
            if not file_id:
                return {"success": False, "error": "Failed to download/save image"}
            
            # Step 6: Create generation document
            print("\n6️⃣ CREATING GENERATION DOCUMENT...")
            post_id = str(sample_data["post_data"]["_id"])
            image_ref_id = self.create_generation_document(post_id, file_id, pipeline_data)
            if not image_ref_id:
                return {"success": False, "error": "Failed to create generation document"}
            
            # Step 7: Update post
            print("\n7️⃣ UPDATING POST...")
            post_updated = self.update_post_with_vlm_generation(post_id, image_ref_id, pipeline_data)
            if not post_updated:
                return {"success": False, "error": "Failed to update post"}
            
            # Success!
            print("\n🎉 PIPELINE COMPLETE!")
            print("=" * 60)
            print(f"✅ Successfully generated new image using VLM pipeline")
            print(f"📸 Original post: {sample_data['shortcode']}")
            print(f"🔍 VLM description: {vlm_result['description'][:100]}...")
            print(f"🎨 Brand prompt: {brand_prompt[:100]}...")
            print(f"🖼️  New image: {flux_result['image_url'][:60]}...")
            print(f"💰 Cost: ${flux_result['cost']:.4f}")
            print(f"💾 Saved to GridFS: {file_id}")
            print(f"📄 Generation document: {image_ref_id}")
            
            return {
                "success": True,
                "post_shortcode": sample_data["shortcode"],
                "instagram_url": sample_data["instagram_url"],
                "vlm_description": vlm_result["description"],
                "brand_prompt": brand_prompt,
                "new_image_url": flux_result["image_url"],
                "file_id": file_id,
                "image_ref_id": str(image_ref_id),
                "cost": flux_result["cost"],
                "models_used": {
                    "vlm": vlm_model,
                    "generation": flux_model
                }
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            if self.client:
                self.client.close()

async def main():
    """Run the VLM to Flux pipeline demo"""
    
    # Get API token
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize pipeline
    pipeline = VLMToFluxPipeline(replicate_token)
    
    # Run pipeline with different configurations
    configurations = [
        {"vlm_model": "blip", "flux_model": "flux-schnell", "prompt_style": "simple"},
        {"vlm_model": "llava", "flux_model": "flux-schnell", "prompt_style": "advanced"},
        # {"vlm_model": "llava", "flux_model": "flux-dev", "prompt_style": "experimental"},  # More expensive
    ]
    
    for i, config in enumerate(configurations, 1):
        print(f"\n🔄 RUNNING CONFIGURATION {i}/{len(configurations)}")
        print(f"Configuration: {config}")
        
        result = await pipeline.run_complete_pipeline(**config)
        
        if result["success"]:
            print(f"✅ Configuration {i} completed successfully!")
        else:
            print(f"❌ Configuration {i} failed: {result['error']}")
        
        # Add delay between runs
        if i < len(configurations):
            print("⏳ Waiting 10 seconds before next configuration...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())