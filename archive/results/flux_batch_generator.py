#!/usr/bin/env python3
"""
Improved Flux Schnell Batch Image Generator

Optimized for generating large batches of images efficiently
with better error handling and progress tracking.
"""

import os
import asyncio
import random
from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId
from pymongo import MongoClient
from gridfs import GridFS

class FluxBatchGenerator:
    """Optimized Flux Schnell batch image generator"""
    
    def __init__(self, replicate_token: str, batch_size: int = 10):
        self.replicate_token = replicate_token
        self.batch_size = batch_size
        self.client = None
        self.db = None
        self.fs = None
        self.session_stats = {
            "total_generated": 0,
            "total_failed": 0,
            "total_cost": 0.0,
            "start_time": datetime.now()
        }
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient('mongodb://192.168.0.22:27017/')
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to instagram_db")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def get_posts_batch(self, limit: int) -> List[Dict[str, Any]]:
        """Get a batch of posts needing images"""
        try:
            posts = list(self.db.posts.find({
                "image_ref": {"$exists": False},
                "instagram_status": {"$in": ["no_status", None]}
            }).limit(limit))
            
            result = []
            for post in posts:
                result.append({
                    "post_id": str(post["_id"]),
                    "shortcode": post.get("shortcode", "unknown"),
                    "caption": post.get("caption", ""),
                    "raw_post": post
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting posts: {e}")
            return []
    
    def generate_enhanced_prompt(self, post_data: Dict[str, Any]) -> str:
        """Generate enhanced brand-consistent prompts"""
        
        # Core SiliconSentiments themes (expanded)
        tech_themes = [
            "abstract digital consciousness visualization",
            "quantum computing interface design", 
            "neural network data flow patterns",
            "cybernetic circuit board aesthetics",
            "holographic user interface elements",
            "algorithmic pattern recognition art",
            "digital twin reality simulation",
            "artificial intelligence node networks",
            "blockchain transaction visualization",
            "augmented reality overlay graphics"
        ]
        
        # Visual style elements
        style_elements = [
            "clean minimalist composition",
            "geometric precision patterns", 
            "neon accent lighting effects",
            "gradient color transitions",
            "crystalline structure details",
            "metallic surface reflections",
            "holographic transparency layers",
            "particle system dynamics",
            "wireframe structural outlines",
            "ambient occlusion shadows"
        ]
        
        # Color palettes
        color_schemes = [
            "electric blue and cyan tones",
            "purple and magenta gradients", 
            "emerald green circuit patterns",
            "golden amber highlights",
            "silver and chrome metallics",
            "deep space navy backgrounds",
            "prismatic rainbow refractions",
            "monochromatic grayscale depth"
        ]
        
        # Technical quality
        quality_specs = [
            "8K ultra-high resolution",
            "photorealistic rendering quality",
            "professional studio lighting",
            "sharp geometric precision",
            "atmospheric depth effects",
            "volumetric lighting rays"
        ]
        
        # Build comprehensive prompt
        theme = random.choice(tech_themes)
        styles = random.sample(style_elements, 3)
        colors = random.choice(color_schemes)
        quality = random.choice(quality_specs)
        
        # Add caption-based context if available
        caption = post_data.get("caption", "")
        context_hint = ""
        if caption and len(caption) > 20:
            # Extract themes from caption
            if any(word in caption.lower() for word in ["ai", "artificial", "intelligence"]):
                context_hint = "artificial intelligence themed, "
            elif any(word in caption.lower() for word in ["data", "algorithm", "code"]):
                context_hint = "data visualization focused, "
            elif any(word in caption.lower() for word in ["future", "tech", "digital"]):
                context_hint = "futuristic technology concept, "
        
        prompt = f"{context_hint}{theme}, {', '.join(styles)}, {colors}, {quality}, Instagram-ready composition, SiliconSentiments brand aesthetic"
        
        return prompt
    
    async def generate_with_flux(self, prompt: str, post_id: str) -> Dict[str, Any]:
        """Generate image using Flux Schnell"""
        try:
            import replicate
            
            # Generate image
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "num_outputs": 1,
                    "num_inference_steps": 4,
                    "width": 1024,
                    "height": 1024
                }
            )
            
            # Get image URL
            image_url = str(output[0]) if isinstance(output, list) else str(output)
            
            # Download image
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return {
                            "success": True,
                            "image_url": image_url,
                            "image_data": image_data,
                            "prompt": prompt,
                            "provider": "replicate_flux_schnell",
                            "cost": 0.003
                        }
            
            return {"success": False, "error": "Failed to download image"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_to_gridfs(self, image_data: bytes, metadata: Dict[str, Any]) -> str:
        """Save image to GridFS with metadata"""
        try:
            file_id = self.fs.put(
                image_data,
                filename=f"flux_schnell_{metadata['post_id']}.png",
                contentType="image/png",
                metadata={
                    **metadata,
                    "generated_at": datetime.now(timezone.utc),
                    "brand": "siliconsentiments",
                    "automated": True,
                    "generator_version": "3.0",
                    "model": "flux-schnell"
                }
            )
            
            return str(file_id)
            
        except Exception as e:
            print(f"   ❌ GridFS save failed: {e}")
            return None
    
    def create_image_document(self, post_id: str, file_id: str, generation_data: Dict[str, Any]) -> str:
        """Create standardized post_images document"""
        try:
            # Use the new standardized structure
            post_images_doc = {
                "images": [{
                    "midjourney_generations": [{
                        "variation": "flux_schnell_v1.0",
                        "prompt": generation_data["prompt"],
                        "image_url": generation_data["image_url"],
                        "timestamp": datetime.now(timezone.utc),
                        "message_id": f"flux_auto_{post_id}",
                        "grid_message_id": f"flux_grid_{post_id}",
                        "variant_idx": 1,
                        "options": {
                            "automated": True, 
                            "provider": "replicate",
                            "model": "flux-schnell",
                            "version": "1.0"
                        },
                        "file_id": file_id,
                        "midjourney_image_id": file_id
                    }]
                }],
                "status": "generated_automated",
                "created_at": datetime.now(timezone.utc),
                "automation_info": {
                    "generated_by": "siliconsentiments_flux_automation",
                    "cost": generation_data["cost"],
                    "provider": generation_data["provider"],
                    "model": "flux-schnell",
                    "version": "3.0",
                    "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            }
            
            # Insert document
            result = self.db.post_images.insert_one(post_images_doc)
            return result.inserted_id
            
        except Exception as e:
            print(f"   ❌ Failed to create image document: {e}")
            return None
    
    def update_post_with_image(self, post_id: str, image_ref_id: str, generation_data: Dict[str, Any]) -> bool:
        """Update post with image reference"""
        try:
            update_result = self.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "image_ref": image_ref_id,
                        "instagram_status": "ready_to_publish",
                        "automation_data": {
                            "generated_at": datetime.now(timezone.utc),
                            "provider": generation_data["provider"],
                            "cost": generation_data["cost"],
                            "prompt": generation_data["prompt"],
                            "automated": True,
                            "model": "flux-schnell",
                            "version": "3.0"
                        },
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return update_result.modified_count > 0
            
        except Exception as e:
            print(f"   ❌ Post update failed: {e}")
            return False
    
    async def process_single_post(self, post: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
        """Process a single post"""
        shortcode = post['shortcode']
        print(f"\n📸 Post {index}/{total}: {shortcode}")
        
        try:
            # Generate prompt
            prompt = self.generate_enhanced_prompt(post)
            print(f"   🎨 Prompt: {prompt[:80]}...")
            
            # Generate image
            gen_result = await self.generate_with_flux(prompt, post['post_id'])
            
            if gen_result["success"]:
                # Save to GridFS
                file_id = self.save_to_gridfs(gen_result["image_data"], {
                    "post_id": post['post_id'],
                    "shortcode": shortcode,
                    "prompt": prompt
                })
                
                if file_id:
                    # Create image document
                    image_ref_id = self.create_image_document(post['post_id'], file_id, gen_result)
                    
                    if image_ref_id:
                        # Update post
                        if self.update_post_with_image(post['post_id'], image_ref_id, gen_result):
                            print(f"   ✅ Success! Cost: ${gen_result['cost']:.4f}")
                            return {
                                "success": True,
                                "post_id": post['post_id'],
                                "shortcode": shortcode,
                                "cost": gen_result['cost']
                            }
            
            print(f"   ❌ Failed: {gen_result.get('error', 'Unknown error')}")
            return {"success": False, "post_id": post['post_id'], "error": gen_result.get('error')}
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return {"success": False, "post_id": post['post_id'], "error": str(e)}
    
    async def generate_batch(self) -> Dict[str, Any]:
        """Generate a batch of images"""
        posts = self.get_posts_batch(self.batch_size)
        
        if not posts:
            return {"message": "No posts need images", "generated": 0}
        
        print(f"🎯 Processing batch of {len(posts)} posts...")
        
        # Process posts concurrently (but with limit to avoid rate limits)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent generations
        
        async def process_with_semaphore(post, index):
            async with semaphore:
                return await self.process_single_post(post, index + 1, len(posts))
        
        # Execute batch
        tasks = [process_with_semaphore(post, i) for i, post in enumerate(posts)]
        results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        total_cost = sum(r.get("cost", 0) for r in successful)
        
        # Update session stats
        self.session_stats["total_generated"] += len(successful)
        self.session_stats["total_failed"] += len(failed)
        self.session_stats["total_cost"] += total_cost
        
        return {
            "attempted": len(posts),
            "successful": len(successful),
            "failed": len(failed),
            "batch_cost": total_cost,
            "details": results
        }
    
    def print_session_summary(self):
        """Print session summary"""
        elapsed = datetime.now() - self.session_stats["start_time"]
        
        print(f"\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {elapsed}")
        print(f"✅ Generated: {self.session_stats['total_generated']}")
        print(f"❌ Failed: {self.session_stats['total_failed']}")
        print(f"💰 Total cost: ${self.session_stats['total_cost']:.4f}")
        
        remaining = self.db.posts.count_documents({
            "image_ref": {"$exists": False}
        })
        print(f"📈 Remaining posts: {remaining}")
        print(f"💡 Estimated remaining cost: ${remaining * 0.003:.2f}")
    
    def close(self):
        """Close connections"""
        if self.client:
            self.client.close()

async def main():
    print("🚀 FLUX SCHNELL BATCH GENERATOR V3.0")
    print("=" * 60)
    
    # Get API token
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize generator
    generator = FluxBatchGenerator(api_token, batch_size=10)
    
    try:
        # Connect to MongoDB
        if not generator.connect_to_mongodb():
            return
        
        # Show current status
        total_posts = generator.db.posts.count_documents({})
        posts_with_images = generator.db.posts.count_documents({"image_ref": {"$exists": True}})
        posts_needing_images = total_posts - posts_with_images
        
        print(f"📊 Current Status:")
        print(f"   Total posts: {total_posts:,}")
        print(f"   Posts with images: {posts_with_images:,}")
        print(f"   Posts needing images: {posts_needing_images:,}")
        
        # Generate batch
        print(f"\n🎨 Starting batch generation...")
        result = await generator.generate_batch()
        
        # Print results
        print(f"\n" + "=" * 60)
        print("📊 BATCH RESULTS")
        print("=" * 60)
        print(f"🎯 Attempted: {result['attempted']}")
        print(f"✅ Successful: {result['successful']}")
        print(f"❌ Failed: {result['failed']}")
        print(f"💰 Batch cost: ${result['batch_cost']:.4f}")
        
        # Session summary
        generator.print_session_summary()
        
    finally:
        generator.close()

if __name__ == "__main__":
    asyncio.run(main())