#!/usr/bin/env python3
"""
Generate Missing Images for SiliconSentiments Posts

This script connects to your Pi MongoDB, finds posts without images,
and generates them using the multi-provider image generation system.
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId

# Add image generator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ss_automation', 'components', 'image_generator', 'src'))

# Custom JSON encoder
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return str(obj)
        return super().default(obj)

class SiliconSentimentsImageGenerator:
    """Generate images for posts missing them"""
    
    def __init__(self, mongodb_uri: str, replicate_token: str):
        """
        Initialize image generator
        
        Args:
            mongodb_uri: MongoDB connection string
            replicate_token: Replicate API token
        """
        self.mongodb_uri = mongodb_uri
        self.replicate_token = replicate_token
        self.client = None
        self.db = None
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            from pymongo import MongoClient
            from gridfs import GridFS
            
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['silicon_sentiments']
            self.fs = GridFS(self.db)
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def get_posts_needing_images(self) -> List[Dict[str, Any]]:
        """Get posts that need images"""
        try:
            posts = list(self.db.posts.find({"image_ref": {"$exists": False}}))
            
            result = []
            for post in posts:
                result.append({
                    "post_id": str(post["_id"]),
                    "shortcode": post.get("shortcode", "unknown"),
                    "created_at": post.get("created_at"),
                    "status": post.get("instagram_status", "no_status"),
                    "raw_post": post
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting posts: {e}")
            return []
    
    def generate_brand_prompt(self, post_data: Dict[str, Any]) -> str:
        """
        Generate SiliconSentiments brand-appropriate prompt
        
        Args:
            post_data: Post information
            
        Returns:
            str: Brand-optimized prompt
        """
        # SiliconSentiments brand themes
        themes = [
            "futuristic digital landscape with silicon circuit patterns",
            "abstract technological visualization in modern style", 
            "minimalist tech-inspired geometric composition",
            "digital consciousness representation with clean aesthetics",
            "neural network visualization in vibrant colors",
            "quantum computing concept art with tech elements",
            "silicon valley inspired digital art",
            "abstract data flow visualization",
            "modern technological interface design",
            "futuristic AI consciousness artwork"
        ]
        
        # Pick a theme (you could make this more sophisticated)
        import random
        selected_theme = random.choice(themes)
        
        # Brand style elements
        style_elements = [
            "digital art",
            "modern aesthetic", 
            "clean minimalist design",
            "tech-inspired",
            "vibrant colors",
            "high contrast",
            "visually striking",
            "instagram ready",
            "professional quality"
        ]
        
        # Combine theme with brand elements
        prompt = f"{selected_theme}, {', '.join(style_elements[:6])}"
        
        return prompt
    
    async def generate_with_replicate(self, prompt: str, post_id: str) -> Dict[str, Any]:
        """
        Generate image using Replicate API
        
        Args:
            prompt: Image generation prompt
            post_id: Post ID for metadata
            
        Returns:
            Dict with generation result
        """
        try:
            import replicate
            
            # Set API token
            replicate.api_token = self.replicate_token
            
            print(f"🎨 Generating image with Replicate...")
            print(f"   Prompt: {prompt[:100]}...")
            
            # Use Flux Schnell for fast generation
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
            image_url = output[0] if isinstance(output, list) else output
            
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
                            "cost": 0.003  # Approximate cost
                        }
            
            return {"success": False, "error": "Failed to download image"}
            
        except Exception as e:
            print(f"❌ Replicate generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def save_to_gridfs(self, image_data: bytes, metadata: Dict[str, Any]) -> str:
        """
        Save image to GridFS
        
        Args:
            image_data: Binary image data
            metadata: Image metadata
            
        Returns:
            str: GridFS file ID
        """
        try:
            # Save to GridFS
            file_id = self.fs.put(
                image_data,
                filename=f"generated_{metadata['post_id']}.png",
                contentType="image/png",
                metadata={
                    **metadata,
                    "generated_at": datetime.now(timezone.utc),
                    "brand": "siliconsentiments",
                    "automation_version": "1.0"
                }
            )
            
            print(f"💾 Saved to GridFS: {file_id}")
            return str(file_id)
            
        except Exception as e:
            print(f"❌ GridFS save failed: {e}")
            return None
    
    def update_post_with_image(self, post_id: str, image_file_id: str, generation_data: Dict[str, Any]) -> bool:
        """
        Update post with generated image reference
        
        Args:
            post_id: Post ID to update
            image_file_id: GridFS file ID
            generation_data: Generation metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Create or update post_images document
            post_images_doc = {
                "images": [{
                    "midjourney_generations": [{
                        "variation": "replicate_flux_schnell",
                        "midjourney_image_id": image_file_id,
                        "prompt": generation_data["prompt"],
                        "post_id": post_id,
                        "generated_at": datetime.now(timezone.utc),
                        "provider": generation_data["provider"],
                        "cost": generation_data["cost"]
                    }]
                }],
                "status": "generated",
                "created_at": datetime.now(timezone.utc)
            }
            
            # Insert post_images document
            result = self.db.post_images.insert_one(post_images_doc)
            image_ref_id = result.inserted_id
            
            # Update post with image_ref
            update_result = self.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$set": {
                        "image_ref": image_ref_id,
                        "instagram_status": "ready_to_publish",
                        "automated_generation": {
                            "generated_at": datetime.now(timezone.utc),
                            "provider": generation_data["provider"],
                            "cost": generation_data["cost"],
                            "prompt": generation_data["prompt"]
                        }
                    }
                }
            )
            
            print(f"📝 Updated post {post_id} with image reference")
            return update_result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Post update failed: {e}")
            return False
    
    async def generate_missing_images(self) -> Dict[str, Any]:
        """
        Generate images for all posts that need them
        
        Returns:
            Dict with generation results
        """
        # Get posts needing images
        posts_needing_images = self.get_posts_needing_images()
        
        if not posts_needing_images:
            return {"message": "No posts need images", "generated": 0}
        
        print(f"🎯 Found {len(posts_needing_images)} posts needing images")
        
        results = {
            "total_attempted": len(posts_needing_images),
            "successful": 0,
            "failed": 0,
            "details": [],
            "total_cost": 0.0
        }
        
        for i, post in enumerate(posts_needing_images, 1):
            print(f"\n📸 Processing post {i}/{len(posts_needing_images)}")
            print(f"   Post ID: {post['post_id']}")
            print(f"   Shortcode: {post['shortcode']}")
            
            try:
                # Generate brand-appropriate prompt
                prompt = self.generate_brand_prompt(post)
                
                # Generate image
                generation_result = await self.generate_with_replicate(prompt, post['post_id'])
                
                if generation_result["success"]:
                    # Save to GridFS
                    file_id = self.save_to_gridfs(
                        generation_result["image_data"],
                        {
                            "post_id": post['post_id'],
                            "prompt": prompt,
                            "provider": generation_result["provider"]
                        }
                    )
                    
                    if file_id:
                        # Update post
                        if self.update_post_with_image(post['post_id'], file_id, generation_result):
                            results["successful"] += 1
                            results["total_cost"] += generation_result["cost"]
                            
                            results["details"].append({
                                "post_id": post['post_id'],
                                "shortcode": post['shortcode'],
                                "success": True,
                                "prompt": prompt,
                                "cost": generation_result["cost"],
                                "file_id": file_id
                            })
                            
                            print(f"✅ Successfully generated image for {post['shortcode']}")
                        else:
                            results["failed"] += 1
                            results["details"].append({
                                "post_id": post['post_id'],
                                "success": False,
                                "error": "Failed to update post"
                            })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "post_id": post['post_id'],
                            "success": False,
                            "error": "Failed to save to GridFS"
                        })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "post_id": post['post_id'],
                        "success": False,
                        "error": generation_result["error"]
                    })
                    
            except Exception as e:
                print(f"❌ Error processing post {post['shortcode']}: {e}")
                results["failed"] += 1
                results["details"].append({
                    "post_id": post['post_id'],
                    "success": False,
                    "error": str(e)
                })
            
            # Small delay between generations
            if i < len(posts_needing_images):
                await asyncio.sleep(2)
        
        return results
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

async def main():
    """Main function"""
    print("🚀 SILICONSENTIMENTS IMAGE GENERATOR")
    print("="*50)
    
    # Configuration
    mongodb_uri = "mongodb://192.168.0.22:27017/"  # Your Pi's IP
    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable required")
        print("   Set it with: export REPLICATE_API_TOKEN='your_token_here'")
        return
    
    # Initialize generator
    generator = SiliconSentimentsImageGenerator(mongodb_uri, replicate_token)
    
    # Connect to MongoDB
    if not generator.connect_to_mongodb():
        return
    
    try:
        # Generate missing images
        results = await generator.generate_missing_images()
        
        # Display results
        print(f"\n" + "="*50)
        print("📊 GENERATION RESULTS")
        print("="*50)
        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"💰 Total cost: ${results['total_cost']:.4f}")
        
        if results['successful'] > 0:
            print(f"\n🎉 SUCCESS! Generated {results['successful']} images")
            print("Your posts are now ready for Instagram publishing!")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} generations failed:")
            for detail in results['details']:
                if not detail['success']:
                    print(f"   • {detail['post_id']}: {detail['error']}")
    
    finally:
        generator.close()

if __name__ == "__main__":
    # Install required packages
    import subprocess
    required_packages = ["replicate", "aiohttp"]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    asyncio.run(main())