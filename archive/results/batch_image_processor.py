#!/usr/bin/env python3
"""
Batch Image Processor using the new SiliconSentiments Image Generation System

Processes multiple posts with different providers and models while maintaining
standardized Midjourney-compatible metadata structure.
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from image_generation_system import SiliconSentimentsImageSystem

class BatchImageProcessor:
    """Process multiple images in batches with different providers/models"""
    
    def __init__(self, replicate_token: str, gemini_token: str = None):
        self.system = SiliconSentimentsImageSystem(replicate_token, gemini_token)
        self.session_stats = {
            "total_attempted": 0,
            "total_successful": 0,
            "total_failed": 0,
            "total_cost": 0.0,
            "by_provider": {},
            "start_time": datetime.now()
        }
    
    async def process_batch(
        self, 
        batch_size: int = 10,
        provider_mix: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a batch with mixed providers/models"""
        
        if not self.system.connect_to_mongodb():
            return {"success": False, "error": "Database connection failed"}
        
        # Default provider mix if not specified
        if provider_mix is None:
            provider_mix = [
                {"provider": "replicate", "model": "flux-schnell", "weight": 0.7},  # 70% Flux Schnell (fast/cheap)
                {"provider": "replicate", "model": "flux-dev", "weight": 0.2},     # 20% Flux Dev (higher quality)
                {"provider": "replicate", "model": "sdxl", "weight": 0.1}         # 10% SDXL (alternative style)
            ]
        
        # Get posts that need images
        posts = list(self.system.db.posts.find({
            "image_ref": {"$exists": False},
            "instagram_status": {"$in": ["no_status", None]}
        }).limit(batch_size))
        
        if not posts:
            return {"success": False, "message": "No posts need images"}
        
        print(f"🎯 Processing batch of {len(posts)} posts with mixed providers")
        print(f"📊 Provider mix: {provider_mix}")
        
        # Assign providers to posts based on weights
        import random
        
        assigned_posts = []
        for post in posts:
            # Choose provider based on weights
            rand = random.random()
            cumulative = 0
            chosen_config = provider_mix[0]  # fallback
            
            for config in provider_mix:
                cumulative += config["weight"]
                if rand <= cumulative:
                    chosen_config = config
                    break
            
            assigned_posts.append({
                "post_id": str(post["_id"]),
                "shortcode": post.get("shortcode", "unknown"),
                "provider": chosen_config["provider"],
                "model": chosen_config["model"],
                "post_data": post
            })
        
        # Process with concurrency control
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent generations
        
        async def process_single_with_semaphore(assignment):
            async with semaphore:
                return await self.process_single_assignment(assignment)
        
        # Execute batch
        tasks = [process_single_with_semaphore(assignment) for assignment in assigned_posts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = []
        failed = []
        
        for result in results:
            if isinstance(result, Exception):
                failed.append({"error": str(result)})
            elif result.get("success"):
                successful.append(result)
            else:
                failed.append(result)
        
        # Update stats
        self.session_stats["total_attempted"] += len(posts)
        self.session_stats["total_successful"] += len(successful)
        self.session_stats["total_failed"] += len(failed)
        
        batch_cost = sum(r.get("cost", 0) for r in successful)
        self.session_stats["total_cost"] += batch_cost
        
        # Update provider stats
        for result in successful:
            provider_key = f"{result['provider']}_{result['model']}"
            if provider_key not in self.session_stats["by_provider"]:
                self.session_stats["by_provider"][provider_key] = {"count": 0, "cost": 0}
            self.session_stats["by_provider"][provider_key]["count"] += 1
            self.session_stats["by_provider"][provider_key]["cost"] += result.get("cost", 0)
        
        return {
            "success": True,
            "attempted": len(posts),
            "successful": len(successful),
            "failed": len(failed),
            "batch_cost": batch_cost,
            "results": successful,
            "errors": failed
        }
    
    async def process_single_assignment(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single post with assigned provider/model"""
        try:
            post_id = assignment["post_id"]
            provider = assignment["provider"]
            model = assignment["model"]
            shortcode = assignment["shortcode"]
            
            print(f"\n📸 {shortcode}: {provider}/{model}")
            
            # Use post caption as context for description if available
            post_data = assignment["post_data"]
            custom_description = None
            if post_data.get("caption") and len(post_data["caption"]) > 50:
                custom_description = f"Instagram post: {post_data['caption'][:200]}"
            
            result = await self.system.analyze_and_generate(
                post_id=post_id,
                provider=provider,
                model=model,
                custom_description=custom_description
            )
            
            result["assignment"] = assignment
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "assignment": assignment
            }
    
    def print_session_summary(self):
        """Print comprehensive session summary"""
        elapsed = datetime.now() - self.session_stats["start_time"]
        
        print(f"\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {elapsed}")
        print(f"🎯 Attempted: {self.session_stats['total_attempted']}")
        print(f"✅ Successful: {self.session_stats['total_successful']}")
        print(f"❌ Failed: {self.session_stats['total_failed']}")
        print(f"💰 Total cost: ${self.session_stats['total_cost']:.4f}")
        
        if self.session_stats["by_provider"]:
            print(f"\n📋 BY PROVIDER:")
            for provider_key, stats in self.session_stats["by_provider"].items():
                print(f"   {provider_key}: {stats['count']} images, ${stats['cost']:.4f}")
        
        # Show remaining work
        try:
            remaining = self.system.db.posts.count_documents({
                "image_ref": {"$exists": False}
            })
            print(f"\n📈 Remaining posts: {remaining}")
            print(f"💡 Est. remaining cost (Flux Schnell): ${remaining * 0.003:.2f}")
            print(f"💡 Est. remaining cost (Mixed): ${remaining * 0.01:.2f}")
        except:
            pass
    
    def close(self):
        """Close connections"""
        self.system.close()

async def run_mixed_provider_batch():
    """Run a batch with mixed providers"""
    print("🚀 SILICONSENTIMENTS MIXED PROVIDER BATCH GENERATOR")
    print("=" * 60)
    
    # Get API tokens
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    gemini_token = os.getenv("GEMINI_API_KEY")  # Optional
    
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    processor = BatchImageProcessor(replicate_token, gemini_token)
    
    try:
        # Show current status
        if processor.system.connect_to_mongodb():
            total_posts = processor.system.db.posts.count_documents({})
            posts_with_images = processor.system.db.posts.count_documents({"image_ref": {"$exists": True}})
            posts_needing_images = total_posts - posts_with_images
            
            print(f"📊 Current Status:")
            print(f"   Total posts: {total_posts:,}")
            print(f"   Posts with images: {posts_with_images:,}")
            print(f"   Posts needing images: {posts_needing_images:,}")
        
        # Define provider mix strategy
        provider_mix = [
            {"provider": "replicate", "model": "flux-schnell", "weight": 0.8},  # 80% fast/cheap
            {"provider": "replicate", "model": "flux-dev", "weight": 0.15},    # 15% high quality
            {"provider": "replicate", "model": "sdxl", "weight": 0.05}         # 5% alternative
        ]
        
        print(f"\n🎨 Starting mixed provider batch generation...")
        
        # Process batch
        result = await processor.process_batch(
            batch_size=10,
            provider_mix=provider_mix
        )
        
        if result["success"]:
            print(f"\n" + "=" * 60)
            print("📊 BATCH RESULTS")
            print("=" * 60)
            print(f"🎯 Attempted: {result['attempted']}")
            print(f"✅ Successful: {result['successful']}")
            print(f"❌ Failed: {result['failed']}")
            print(f"💰 Batch cost: ${result['batch_cost']:.4f}")
            
            if result["results"]:
                print(f"\n📸 Generated Images:")
                for r in result["results"]:
                    print(f"   {r['shortcode']}: {r['provider']}/{r['model']} (${r['cost']:.4f})")
            
            if result["errors"]:
                print(f"\n❌ Errors:")
                for e in result["errors"]:
                    print(f"   {e.get('error', 'Unknown error')}")
        else:
            print(f"❌ Batch failed: {result.get('error', 'Unknown error')}")
        
        # Session summary
        processor.print_session_summary()
        
    finally:
        processor.close()

async def run_quality_focused_batch():
    """Run a batch focused on higher quality models"""
    print("🎨 QUALITY-FOCUSED BATCH GENERATION")
    print("=" * 50)
    
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    processor = BatchImageProcessor(replicate_token)
    
    try:
        # High-quality provider mix
        quality_mix = [
            {"provider": "replicate", "model": "flux-dev", "weight": 0.6},     # 60% Flux Dev
            {"provider": "replicate", "model": "flux-pro", "weight": 0.3},     # 30% Flux Pro  
            {"provider": "replicate", "model": "sdxl", "weight": 0.1}          # 10% SDXL
        ]
        
        result = await processor.process_batch(
            batch_size=5,  # Smaller batch for expensive models
            provider_mix=quality_mix
        )
        
        if result["success"]:
            print(f"✅ Quality batch complete: {result['successful']} images, ${result['batch_cost']:.4f}")
        else:
            print(f"❌ Quality batch failed: {result.get('error')}")
        
        processor.print_session_summary()
        
    finally:
        processor.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quality":
        asyncio.run(run_quality_focused_batch())
    else:
        asyncio.run(run_mixed_provider_batch())