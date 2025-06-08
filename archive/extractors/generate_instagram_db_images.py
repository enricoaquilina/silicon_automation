#!/usr/bin/env python3
"""
Generate Images for Instagram DB Posts

This script generates images for posts in the main instagram_db database
that are missing images, focusing on getting SiliconSentiments back to daily posting.
"""

import os
import sys
import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId

class SiliconSentimentsInstagramGenerator:
    """Generate images for Instagram DB posts"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.client = None
        self.db = None
        self.fs = None
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            from pymongo import MongoClient
            from gridfs import GridFS
            
            self.client = MongoClient('mongodb://192.168.0.22:27017/')
            self.db = self.client['instagram_db']  # Main database
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to instagram_db")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def get_posts_needing_images(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get posts that need images"""
        try:
            # Get posts without image_ref, prioritizing those with no_status
            posts = list(self.db.posts.find({
                "image_ref": {"$exists": False},
                "instagram_status": {"$in": ["no_status", None]}
            }).limit(limit))
            
            result = []
            for post in posts:
                result.append({
                    "post_id": str(post["_id"]),
                    "shortcode": post.get("shortcode", "unknown"),
                    "instagram_status": post.get("instagram_status", "no_status"),
                    "raw_post": post
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting posts: {e}")
            return []
    
    def generate_siliconsentiments_prompt(self) -> str:
        """Generate brand-consistent prompts for SiliconSentiments"""
        
        # Core SiliconSentiments themes
        core_themes = [
            "futuristic digital landscape with silicon circuit patterns",
            "abstract technological visualization in modern minimalist style",
            "neural network consciousness representation",
            "quantum computing concept art with geometric elements", 
            "digital data flow visualization with clean aesthetics",
            "silicon valley inspired tech art with vibrant gradients",
            "AI consciousness visualization in abstract form",
            "modern technological interface design with depth",
            "cybernetic digital art with tech-inspired elements",
            "abstract computational visualization with modern style"
        ]
        
        # Style modifiers for brand consistency  
        style_elements = [
            "digital art",
            "modern aesthetic",
            "clean minimalist design", 
            "tech-inspired",
            "silicon valley vibes",
            "vibrant colors",
            "high contrast",
            "professional quality",
            "instagram ready",
            "visually striking"
        ]
        
        # Technical quality enhancers
        quality_terms = [
            "8k resolution",
            "highly detailed",
            "sharp focus",
            "professional photography",
            "studio lighting"
        ]
        
        # Build prompt
        theme = random.choice(core_themes)
        styles = random.sample(style_elements, 5)  # Pick 5 style elements
        quality = random.choice(quality_terms)
        
        prompt = f"{theme}, {', '.join(styles)}, {quality}"
        
        return prompt
    
    async def generate_with_replicate(self, prompt: str, post_id: str) -> Dict[str, Any]:
        """Generate image using Replicate"""
        try:
            import replicate
            
            print(f"   🎨 Generating: {prompt[:80]}...")
            
            # Use Flux Schnell for fast, cost-effective generation
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
            
            # Handle FileOutput object
            if isinstance(output, list):
                image_url = str(output[0])
            else:
                image_url = str(output)
            
            print(f"   🔗 Image URL: {image_url}")
            
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
            
            return {"success": False, "error": "Failed to download"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_to_gridfs(self, image_data: bytes, metadata: Dict[str, Any]) -> str:
        """Save image to GridFS"""
        try:
            file_id = self.fs.put(
                image_data,
                filename=f"siliconsentiments_{metadata['post_id']}.png",
                contentType="image/png",
                metadata={
                    **metadata,
                    "generated_at": datetime.now(timezone.utc),
                    "brand": "siliconsentiments",
                    "automated": True,
                    "generator_version": "2.0"
                }
            )
            
            return str(file_id)
            
        except Exception as e:
            print(f"   ❌ GridFS save failed: {e}")
            return None
    
    def update_post_with_image(self, post_id: str, file_id: str, generation_data: Dict[str, Any]) -> bool:
        """Update post with image reference"""
        try:
            print(f"   📝 Updating post with ID: {post_id} (type: {type(post_id)})")
            # Create post_images document
            post_images_doc = {
                "images": [{
                    "midjourney_generations": [{
                        "variation": "replicate_flux_schnell",
                        "prompt": generation_data["prompt"],
                        "image_url": generation_data["image_url"],
                        "timestamp": datetime.now(timezone.utc),
                        "message_id": f"auto_{post_id}",
                        "grid_message_id": f"grid_{post_id}",
                        "variant_idx": 1,
                        "options": {"automated": True, "provider": "replicate"},
                        "file_id": file_id,
                        "midjourney_image_id": file_id
                    }]
                }],
                "status": "generated_automated",
                "created_at": datetime.now(timezone.utc),
                "automation_info": {
                    "generated_by": "siliconsentiments_automation",
                    "cost": generation_data["cost"],
                    "provider": generation_data["provider"]
                }
            }
            
            # Insert post_images document
            result = self.db.post_images.insert_one(post_images_doc)
            image_ref_id = result.inserted_id
            
            # Update post
            update_result = self.db.posts.update_one(
                {"_id": ObjectId(post_id) if isinstance(post_id, str) else post_id},
                {
                    "$set": {
                        "image_ref": image_ref_id,
                        "instagram_status": "ready_to_publish",
                        "automation_data": {
                            "generated_at": datetime.now(timezone.utc),
                            "provider": generation_data["provider"],
                            "cost": generation_data["cost"],
                            "prompt": generation_data["prompt"],
                            "automated": True
                        },
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return update_result.modified_count > 0
            
        except Exception as e:
            print(f"   ❌ Post update failed: {e}")
            return False
    
    async def generate_batch(self, batch_size: int = 1) -> Dict[str, Any]:
        """Generate images for a batch of posts"""
        posts_needing_images = self.get_posts_needing_images(batch_size)
        
        if not posts_needing_images:
            return {"message": "No posts need images", "generated": 0}
        
        print(f"🎯 Processing {len(posts_needing_images)} posts...")
        
        results = {
            "attempted": len(posts_needing_images),
            "successful": 0,
            "failed": 0,
            "total_cost": 0.0,
            "details": []
        }
        
        for i, post in enumerate(posts_needing_images, 1):
            print(f"\n📸 Post {i}/{len(posts_needing_images)}: {post['shortcode']}")
            
            try:
                # Generate brand prompt
                prompt = self.generate_siliconsentiments_prompt()
                
                # Generate image
                gen_result = await self.generate_with_replicate(prompt, post['post_id'])
                
                if gen_result["success"]:
                    # Save to GridFS
                    file_id = self.save_to_gridfs(gen_result["image_data"], {
                        "post_id": post['post_id'],
                        "shortcode": post['shortcode'],
                        "prompt": prompt
                    })
                    
                    if file_id:
                        # Update post
                        if self.update_post_with_image(post['post_id'], file_id, gen_result):
                            results["successful"] += 1
                            results["total_cost"] += gen_result["cost"]
                            print(f"   ✅ Success! Cost: ${gen_result['cost']:.4f}")
                            
                            results["details"].append({
                                "post_id": post['post_id'],
                                "shortcode": post['shortcode'],
                                "success": True,
                                "cost": gen_result["cost"],
                                "file_id": file_id
                            })
                        else:
                            results["failed"] += 1
                            print(f"   ❌ Failed to update post")
                    else:
                        results["failed"] += 1
                        print(f"   ❌ Failed to save to GridFS")
                else:
                    results["failed"] += 1
                    print(f"   ❌ Generation failed: {gen_result['error']}")
                    
            except Exception as e:
                results["failed"] += 1
                print(f"   ❌ Error: {e}")
            
            # Delay between generations
            if i < len(posts_needing_images):
                await asyncio.sleep(2)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current database stats"""
        try:
            total_posts = self.db.posts.count_documents({})
            posts_with_images = self.db.posts.count_documents({"image_ref": {"$exists": True}})
            posts_without_images = self.db.posts.count_documents({"image_ref": {"$exists": False}})
            published_posts = self.db.posts.count_documents({"instagram_status": "published"})
            ready_to_publish = self.db.posts.count_documents({"instagram_status": "ready_to_publish"})
            
            return {
                "total_posts": total_posts,
                "posts_with_images": posts_with_images,
                "posts_without_images": posts_without_images,
                "published_posts": published_posts,
                "ready_to_publish": ready_to_publish
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()

async def main():
    """Main function"""
    print("🚀 SILICONSENTIMENTS INSTAGRAM IMAGE GENERATOR")
    print("=" * 60)
    
    # Get Replicate token
    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize generator
    generator = SiliconSentimentsInstagramGenerator(replicate_token)
    
    # Connect
    if not generator.connect_to_mongodb():
        return
    
    try:
        # Show current stats
        stats = generator.get_stats()
        print(f"📊 Current Status:")
        print(f"   Total posts: {stats.get('total_posts', 0):,}")
        print(f"   Posts with images: {stats.get('posts_with_images', 0):,}")
        print(f"   Posts needing images: {stats.get('posts_without_images', 0):,}")
        print(f"   Published posts: {stats.get('published_posts', 0):,}")
        print(f"   Ready to publish: {stats.get('ready_to_publish', 0):,}")
        
        # Generate batch
        print(f"\n🎨 Starting image generation...")
        
        batch_size = 5  # Start with small batch
        results = await generator.generate_batch(batch_size)
        
        # Results
        print(f"\n" + "=" * 60)
        print(f"📊 BATCH RESULTS")
        print(f"=" * 60)
        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"💰 Total cost: ${results['total_cost']:.4f}")
        
        if results['successful'] > 0:
            print(f"\n🎉 Generated {results['successful']} images!")
            print(f"📈 Progress: {results['successful']} more posts ready for publishing")
            
            # Updated stats
            updated_stats = generator.get_stats()
            remaining = updated_stats.get('posts_without_images', 0)
            print(f"📊 Remaining posts needing images: {remaining:,}")
            
            if remaining > 0:
                estimated_cost = remaining * 0.003
                print(f"💡 To generate all remaining images:")
                print(f"   Estimated cost: ${estimated_cost:.2f}")
                print(f"   Run this script multiple times or increase batch_size")
    
    finally:
        generator.close()

if __name__ == "__main__":
    asyncio.run(main())