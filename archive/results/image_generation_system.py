#!/usr/bin/env python3
"""
SiliconSentiments Image Generation System

A comprehensive module that:
1. Analyzes existing images to extract descriptions
2. Formulates brand-consistent prompts
3. Generates images with multiple providers (Replicate/Midjourney/Gemini/etc)
4. Saves with standardized Midjourney-compatible metadata structure
"""

import os
import asyncio
import base64
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from pymongo import MongoClient
from gridfs import GridFS
import json

class ImageDescriptionAnalyzer:
    """Analyzes images to extract descriptions using vision models"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
    
    async def analyze_image_with_gemini(self, image_data: bytes) -> str:
        """Analyze image using Gemini Vision to get description"""
        try:
            import google.generativeai as genai
            
            if not self.gemini_api_key:
                return "No Gemini API key provided"
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode()
            
            prompt = """Analyze this image and provide a detailed description focusing on:
            1. Visual elements and composition
            2. Color scheme and lighting
            3. Artistic style and technique
            4. Technology or digital themes present
            5. Overall mood and aesthetic
            
            Be specific and descriptive for use in image generation prompts."""
            
            # Note: This is a simplified example - actual Gemini Vision API usage may differ
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_b64}])
            
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            return "Analysis failed"
    
    async def analyze_image_with_replicate(self, image_url: str) -> str:
        """Analyze image using Replicate vision models"""
        try:
            import replicate
            
            # Use BLIP or similar vision model on Replicate
            output = replicate.run(
                "salesforce/blip",
                input={
                    "image": image_url,
                    "task": "image_captioning"
                }
            )
            
            return output if isinstance(output, str) else str(output)
            
        except Exception as e:
            print(f"❌ Replicate analysis failed: {e}")
            return "Analysis failed"

class SiliconSentimentsBrandPromptGenerator:
    """Generates brand-consistent prompts from descriptions"""
    
    def __init__(self):
        # SiliconSentiments brand DNA
        self.brand_themes = {
            "core_concepts": [
                "digital consciousness evolution",
                "quantum computing interfaces", 
                "neural network architectures",
                "cybernetic organism integration",
                "artificial intelligence emergence",
                "blockchain reality matrices",
                "augmented perception layers",
                "algorithmic pattern recognition",
                "holographic data visualization",
                "synthetic biology networks"
            ],
            "visual_styles": [
                "clean geometric minimalism",
                "neon-lit circuit aesthetics", 
                "crystalline structure formations",
                "liquid metal transformations",
                "particle system dynamics",
                "wireframe architectural blueprints",
                "holographic transparency effects",
                "gradient color transitions",
                "ambient lighting atmospheres",
                "precision-engineered surfaces"
            ],
            "color_palettes": [
                "electric blue and cyan harmonies",
                "deep purple and magenta gradients",
                "emerald green circuit patterns",
                "golden amber accent highlights",
                "chrome and silver metallics",
                "prismatic rainbow refractions",
                "monochromatic depth studies",
                "neon pink and teal contrasts"
            ],
            "technical_specs": [
                "8K ultra-resolution clarity",
                "photorealistic rendering quality",
                "volumetric lighting effects",
                "atmospheric depth layering",
                "sharp geometric precision",
                "professional studio composition"
            ]
        }
    
    def generate_brand_prompt(self, description: str, style_preference: str = "balanced") -> str:
        """Generate SiliconSentiments brand prompt from description"""
        import random
        
        # Analyze description for key themes
        tech_keywords = ["digital", "circuit", "data", "network", "tech", "cyber", "ai", "algorithm"]
        has_tech_theme = any(keyword in description.lower() for keyword in tech_keywords)
        
        # Select brand elements
        if style_preference == "minimal":
            core_concept = random.choice(self.brand_themes["core_concepts"][:5])  # More minimal concepts
            visual_styles = random.sample(self.brand_themes["visual_styles"][:3], 2)
        elif style_preference == "complex":
            core_concept = random.choice(self.brand_themes["core_concepts"][5:])  # More complex concepts
            visual_styles = random.sample(self.brand_themes["visual_styles"], 4)
        else:  # balanced
            core_concept = random.choice(self.brand_themes["core_concepts"])
            visual_styles = random.sample(self.brand_themes["visual_styles"], 3)
        
        color_palette = random.choice(self.brand_themes["color_palettes"])
        technical_spec = random.choice(self.brand_themes["technical_specs"])
        
        # Build prompt incorporating original description themes
        if has_tech_theme:
            brand_prompt = f"{core_concept} inspired by {description[:100]}"
        else:
            brand_prompt = f"{core_concept} reimagined as technological art"
        
        brand_prompt += f", {', '.join(visual_styles)}, {color_palette}, {technical_spec}"
        brand_prompt += ", Instagram-ready composition, SiliconSentiments signature aesthetic"
        
        return brand_prompt

class MultiProviderImageGenerator:
    """Generates images using multiple providers with standardized metadata"""
    
    def __init__(self, replicate_token: str = None, gemini_token: str = None):
        self.replicate_token = replicate_token
        self.gemini_token = gemini_token
    
    async def generate_with_replicate_flux(self, prompt: str, model: str = "flux-schnell") -> Dict[str, Any]:
        """Generate with Replicate Flux models"""
        try:
            import replicate
            
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
                },
                "flux-pro": {
                    "model": "black-forest-labs/flux-pro",
                    "cost": 0.055,
                    "params": {"num_inference_steps": 25}
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
            
            return {
                "success": True,
                "image_url": image_url,
                "provider": "replicate",
                "model": model,
                "cost": config["cost"],
                "metadata": {
                    "model_version": config["model"],
                    "inference_steps": config["params"].get("num_inference_steps", 4)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_with_replicate_sdxl(self, prompt: str) -> Dict[str, Any]:
        """Generate with Replicate SDXL"""
        try:
            import replicate
            
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt,
                    "width": 1024,
                    "height": 1024,
                    "num_outputs": 1,
                    "num_inference_steps": 50
                }
            )
            
            image_url = str(output[0]) if isinstance(output, list) else str(output)
            
            return {
                "success": True,
                "image_url": image_url,
                "provider": "replicate",
                "model": "sdxl",
                "cost": 0.0039,
                "metadata": {
                    "model_version": "stability-ai/sdxl",
                    "inference_steps": 50
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_with_gemini_imagen(self, prompt: str) -> Dict[str, Any]:
        """Generate with Gemini Imagen (placeholder - actual implementation depends on API)"""
        try:
            # Note: This is a placeholder - actual Gemini Imagen API may differ
            return {
                "success": False,
                "error": "Gemini Imagen integration not yet implemented"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        return await response.read()
            return None
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

class StandardizedImageStorage:
    """Stores images with standardized Midjourney-compatible metadata structure"""
    
    def __init__(self, db, fs):
        self.db = db
        self.fs = fs
    
    def create_midjourney_compatible_document(
        self, 
        post_id: str, 
        file_id: str, 
        generation_data: Dict[str, Any],
        description: str = "",
        original_prompt: str = ""
    ) -> str:
        """Create document following exact Midjourney template structure"""
        
        provider = generation_data.get("provider", "unknown")
        model = generation_data.get("model", "unknown")
        variation_name = f"{provider}_{model}_v1.0"
        
        # Follow exact Midjourney document structure
        post_images_doc = {
            "_id": ObjectId(),
            "post_id": post_id,
            "images": [{
                "midjourney_generations": [{
                    "variation": variation_name,
                    "prompt": generation_data.get("final_prompt", original_prompt),
                    "timestamp": datetime.now(timezone.utc),
                    "message_id": f"{provider}_auto_{post_id}",
                    "grid_message_id": f"{provider}_grid_{post_id}",
                    "variant_idx": 1,
                    "options": {
                        "automated": True,
                        "provider": provider,
                        "model": model,
                        "original_description": description,
                        "brand_adaptation": "siliconsentiments_v3.0",
                        **generation_data.get("metadata", {})
                    },
                    "file_id": file_id,
                    "midjourney_image_id": file_id,
                    "image_url": generation_data.get("image_url", ""),
                    
                    # Extended metadata for multi-provider support
                    "generation_metadata": {
                        "cost": generation_data.get("cost", 0),
                        "provider_specific": generation_data.get("metadata", {}),
                        "brand_prompt_version": "3.0",
                        "analysis_method": "automated",
                        "quality_score": None  # To be filled by quality assessment
                    }
                }]
            }],
            "created_at": datetime.now(timezone.utc),
            "status": "generated_automated",
            
            # Match legacy structure but with enhanced automation info
            "automation_info": {
                "generated_by": "siliconsentiments_multi_provider_v3.0",
                "cost": generation_data.get("cost", 0),
                "provider": provider,
                "model": model,
                "description_source": "automated_analysis",
                "brand_consistency_score": None,  # To be calculated
                "generation_timestamp": datetime.now(timezone.utc),
                "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        try:
            # Insert document
            result = self.db.post_images.insert_one(post_images_doc)
            return result.inserted_id
            
        except Exception as e:
            print(f"❌ Failed to create image document: {e}")
            return None
    
    def save_image_to_gridfs(
        self, 
        image_data: bytes, 
        metadata: Dict[str, Any], 
        provider: str, 
        model: str
    ) -> str:
        """Save image to GridFS with comprehensive metadata"""
        try:
            filename = f"ss_{provider}_{model}_{metadata.get('post_id', 'unknown')}.png"
            
            file_id = self.fs.put(
                image_data,
                filename=filename,
                contentType="image/png",
                metadata={
                    "brand": "siliconsentiments",
                    "automated": True,
                    "generator_version": "3.0",
                    "provider": provider,
                    "model": model,
                    "generated_at": datetime.now(timezone.utc),
                    "post_id": metadata.get("post_id"),
                    "shortcode": metadata.get("shortcode"),
                    "prompt": metadata.get("prompt", ""),
                    "description": metadata.get("description", ""),
                    "cost": metadata.get("cost", 0),
                    "quality_assessed": False,
                    "brand_consistency_checked": False
                }
            )
            
            return str(file_id)
            
        except Exception as e:
            print(f"❌ GridFS save failed: {e}")
            return None

class SiliconSentimentsImageSystem:
    """Main orchestrator for the complete image generation system"""
    
    def __init__(
        self, 
        replicate_token: str = None, 
        gemini_token: str = None,
        mongodb_uri: str = "mongodb://192.168.0.22:27017/"
    ):
        self.replicate_token = replicate_token
        self.gemini_token = gemini_token
        self.mongodb_uri = mongodb_uri
        
        # Initialize components
        self.analyzer = ImageDescriptionAnalyzer(gemini_token)
        self.prompt_generator = SiliconSentimentsBrandPromptGenerator()
        self.image_generator = MultiProviderImageGenerator(replicate_token, gemini_token)
        
        # Database connections
        self.client = None
        self.db = None
        self.fs = None
        self.storage = None
    
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            self.storage = StandardizedImageStorage(self.db, self.fs)
            
            self.client.admin.command('ping')
            print("✅ Connected to instagram_db")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def analyze_and_generate(
        self, 
        post_id: str, 
        provider: str = "replicate", 
        model: str = "flux-schnell",
        existing_image_url: str = None,
        custom_description: str = None
    ) -> Dict[str, Any]:
        """Complete pipeline: analyze -> prompt -> generate -> save"""
        
        print(f"🎨 Processing post {post_id} with {provider}/{model}")
        
        try:
            # Step 1: Get description
            if custom_description:
                description = custom_description
                print(f"   📝 Using custom description")
            elif existing_image_url:
                description = await self.analyzer.analyze_image_with_replicate(existing_image_url)
                print(f"   🔍 Analyzed existing image")
            else:
                # Get post data for context
                post = self.db.posts.find_one({"_id": ObjectId(post_id)})
                if post and post.get("caption"):
                    description = f"Social media post about: {post['caption'][:200]}"
                else:
                    description = "Digital art with technology themes"
                print(f"   📄 Using post context")
            
            print(f"   📝 Description: {description[:100]}...")
            
            # Step 2: Generate brand prompt
            brand_prompt = self.prompt_generator.generate_brand_prompt(description)
            print(f"   🎯 Brand prompt: {brand_prompt[:100]}...")
            
            # Step 3: Generate image
            if provider == "replicate":
                if model in ["flux-schnell", "flux-dev", "flux-pro"]:
                    gen_result = await self.image_generator.generate_with_replicate_flux(brand_prompt, model)
                elif model == "sdxl":
                    gen_result = await self.image_generator.generate_with_replicate_sdxl(brand_prompt)
                else:
                    return {"success": False, "error": f"Unknown model: {model}"}
            elif provider == "gemini":
                gen_result = await self.image_generator.generate_with_gemini_imagen(brand_prompt)
            else:
                return {"success": False, "error": f"Unknown provider: {provider}"}
            
            if not gen_result["success"]:
                return gen_result
            
            print(f"   🖼️  Generated image: {gen_result['image_url'][:50]}...")
            
            # Step 4: Download image
            image_data = await self.image_generator.download_image(gen_result["image_url"])
            if not image_data:
                return {"success": False, "error": "Failed to download image"}
            
            print(f"   📥 Downloaded {len(image_data)} bytes")
            
            # Step 5: Save to GridFS
            post = self.db.posts.find_one({"_id": ObjectId(post_id)})
            shortcode = post.get("shortcode", "unknown") if post else "unknown"
            
            file_id = self.storage.save_image_to_gridfs(
                image_data,
                {
                    "post_id": post_id,
                    "shortcode": shortcode,
                    "prompt": brand_prompt,
                    "description": description,
                    "cost": gen_result.get("cost", 0)
                },
                provider,
                model
            )
            
            if not file_id:
                return {"success": False, "error": "Failed to save to GridFS"}
            
            print(f"   💾 Saved to GridFS: {file_id}")
            
            # Step 6: Create standardized document
            gen_result["final_prompt"] = brand_prompt
            image_ref_id = self.storage.create_midjourney_compatible_document(
                post_id, file_id, gen_result, description, brand_prompt
            )
            
            if not image_ref_id:
                return {"success": False, "error": "Failed to create image document"}
            
            # Step 7: Update post
            update_result = self.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "image_ref": image_ref_id,
                        "instagram_status": "ready_to_publish",
                        "automation_data": {
                            "generated_at": datetime.now(timezone.utc),
                            "provider": provider,
                            "model": model,
                            "cost": gen_result.get("cost", 0),
                            "prompt": brand_prompt,
                            "description": description,
                            "automated": True,
                            "version": "3.0"
                        },
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            success = update_result.modified_count > 0
            if success:
                print(f"   ✅ Complete! Cost: ${gen_result.get('cost', 0):.4f}")
            
            return {
                "success": success,
                "post_id": post_id,
                "shortcode": shortcode,
                "image_ref_id": str(image_ref_id),
                "file_id": file_id,
                "cost": gen_result.get("cost", 0),
                "provider": provider,
                "model": model,
                "prompt": brand_prompt,
                "description": description
            }
            
        except Exception as e:
            print(f"   ❌ Pipeline failed: {e}")
            return {"success": False, "error": str(e)}
    
    def close(self):
        """Close connections"""
        if self.client:
            self.client.close()

# Example usage functions
async def demo_single_generation():
    """Demo: Generate single image"""
    print("🔬 DEMO: Single Image Generation")
    print("=" * 50)
    
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    system = SiliconSentimentsImageSystem(replicate_token=api_token)
    
    try:
        if not system.connect_to_mongodb():
            return
        
        # Get a post that needs an image
        post = system.db.posts.find_one({"image_ref": {"$exists": False}})
        if not post:
            print("❌ No posts need images")
            return
        
        post_id = str(post["_id"])
        print(f"📝 Using post: {post.get('shortcode', post_id)}")
        
        # Generate with Flux Schnell
        result = await system.analyze_and_generate(
            post_id=post_id,
            provider="replicate", 
            model="flux-schnell"
        )
        
        if result["success"]:
            print(f"✅ Success! Generated image for {result['shortcode']}")
            print(f"💰 Cost: ${result['cost']:.4f}")
        else:
            print(f"❌ Failed: {result['error']}")
            
    finally:
        system.close()

if __name__ == "__main__":
    asyncio.run(demo_single_generation())