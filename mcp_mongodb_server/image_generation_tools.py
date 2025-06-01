"""
Image Generation Integration Tools for MCP Server

This module provides tools to integrate the multi-provider image generation
system with the MongoDB analysis for automated content creation.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Add image generator to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ss_automation', 'components', 'image_generator', 'src'))

try:
    from image_generator.services.multi_provider_service import (
        MultiProviderGenerationService,
        GenerationRequest,
        ProviderStrategy
    )
    IMAGE_GENERATION_AVAILABLE = True
except ImportError:
    IMAGE_GENERATION_AVAILABLE = False
    logging.warning("Image generation system not available")

logger = logging.getLogger("image_generation_tools")


class ImageGenerationIntegration:
    """Integration between MongoDB analysis and image generation"""
    
    def __init__(self, mongodb_client, config: Dict[str, Any]):
        """
        Initialize image generation integration
        
        Args:
            mongodb_client: MongoDB client instance
            config: Configuration for image generation
        """
        self.mongodb = mongodb_client
        self.config = config
        self.generation_service = None
        
    async def initialize_generation_service(self) -> bool:
        """Initialize the multi-provider generation service"""
        if not IMAGE_GENERATION_AVAILABLE:
            logger.error("Image generation system not available")
            return False
        
        try:
            self.generation_service = MultiProviderGenerationService(self.config)
            success = await self.generation_service.initialize()
            
            if success:
                logger.info("Image generation service initialized successfully")
            else:
                logger.error("Failed to initialize image generation service")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing generation service: {e}")
            return False
    
    async def generate_missing_images(self, posts_data: List[Dict[str, Any]], max_generations: int = 5) -> Dict[str, Any]:
        """
        Generate images for posts that are missing them
        
        Args:
            posts_data: List of posts needing images
            max_generations: Maximum number of images to generate
            
        Returns:
            Dict with generation results
        """
        if not self.generation_service:
            return {"error": "Generation service not initialized"}
        
        results = {
            "attempted_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "generation_details": [],
            "total_cost": 0.0
        }
        
        # Limit to max_generations
        posts_to_process = posts_data[:max_generations]
        
        for post in posts_to_process:
            try:
                results["attempted_generations"] += 1
                
                # Generate prompts based on SiliconSentiments style
                prompt = self._generate_brand_prompt(post)
                
                logger.info(f"Generating image for post {post['shortcode']} with prompt: {prompt}")
                
                # Create generation request
                request = GenerationRequest(
                    prompt=prompt,
                    metadata={
                        "post_id": post["post_id"],
                        "shortcode": post["shortcode"],
                        "brand": "siliconsentiments",
                        "platform": "instagram",
                        "generated_via": "mcp_automation"
                    },
                    strategy=ProviderStrategy.BRAND_OPTIMIZED,
                    save_to_storage=True,
                    variations_needed=1
                )
                
                # Generate image
                response = await self.generation_service.generate_image(request)
                
                generation_detail = {
                    "post_id": post["post_id"],
                    "shortcode": post["shortcode"],
                    "prompt": prompt,
                    "success": response.success,
                    "provider_used": response.provider_used,
                    "cost": response.cost,
                    "generation_time": response.generation_time
                }
                
                if response.success:
                    results["successful_generations"] += 1
                    results["total_cost"] += response.cost
                    
                    generation_detail.update({
                        "image_urls": response.image_urls,
                        "storage_ids": response.storage_ids,
                        "generation_id": response.generation_id
                    })
                    
                    # Update MongoDB with generation results
                    await self._update_post_with_generation(
                        post["post_id"], 
                        response
                    )
                else:
                    results["failed_generations"] += 1
                    generation_detail["error"] = response.error
                
                results["generation_details"].append(generation_detail)
                
                # Small delay between generations
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error generating image for post {post['shortcode']}: {e}")
                results["failed_generations"] += 1
                results["generation_details"].append({
                    "post_id": post["post_id"],
                    "shortcode": post["shortcode"],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _generate_brand_prompt(self, post: Dict[str, Any]) -> str:
        """
        Generate a brand-appropriate prompt for a post
        
        Args:
            post: Post data
            
        Returns:
            str: Generated prompt
        """
        # SiliconSentiments brand style elements
        base_styles = [
            "digital art",
            "modern aesthetic", 
            "tech-inspired",
            "clean minimalist design",
            "futuristic elements",
            "abstract geometry",
            "silicon valley vibes"
        ]
        
        # Artistic themes that work well for the brand
        themes = [
            "technological landscape",
            "abstract data visualization", 
            "futuristic cityscape",
            "digital consciousness",
            "silicon circuit patterns",
            "neural network visualization",
            "quantum computing concepts",
            "AI consciousness representation"
        ]
        
        # Pick elements based on post characteristics
        import random
        selected_theme = random.choice(themes)
        selected_styles = random.sample(base_styles, 3)
        
        # Create prompt
        prompt = f"{selected_theme}, {', '.join(selected_styles)}"
        
        # Add Instagram optimization
        prompt += ", vibrant colors, high contrast, visually striking, instagram ready"
        
        return prompt
    
    async def _update_post_with_generation(self, post_id: str, generation_response) -> bool:
        """
        Update MongoDB post with generation results
        
        Args:
            post_id: Post ID to update
            generation_response: Generation response from service
            
        Returns:
            bool: Success status
        """
        try:
            # This would integrate with your existing storage system
            # For now, we'll create a simple update structure
            
            update_data = {
                "automated_generation": {
                    "generated_at": datetime.now(timezone.utc),
                    "provider": generation_response.provider_used,
                    "generation_id": generation_response.generation_id,
                    "storage_ids": generation_response.storage_ids,
                    "cost": generation_response.cost,
                    "status": "completed" if generation_response.success else "failed"
                }
            }
            
            # Update the post document
            result = self.mongodb.db.posts.update_one(
                {"_id": post_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating post {post_id} with generation results: {e}")
            return False
    
    async def analyze_successful_prompts(self) -> Dict[str, Any]:
        """
        Analyze successful prompts to improve future generation
        
        Returns:
            Dict with prompt analysis
        """
        try:
            # Get successful posts with automated generations
            pipeline = [
                {
                    "$match": {
                        "instagram_status": "published",
                        "automated_generation": {"$exists": True}
                    }
                },
                {
                    "$lookup": {
                        "from": "post_images",
                        "localField": "image_ref", 
                        "foreignField": "_id",
                        "as": "image_data"
                    }
                }
            ]
            
            successful_automated_posts = list(self.mongodb.db.posts.aggregate(pipeline))
            
            analysis = {
                "total_automated_posts": len(successful_automated_posts),
                "successful_providers": {},
                "cost_analysis": {
                    "total_cost": 0.0,
                    "avg_cost_per_post": 0.0,
                    "cost_by_provider": {}
                },
                "performance_metrics": {
                    "avg_generation_time": 0.0,
                    "success_rate_by_provider": {}
                }
            }
            
            total_generation_time = 0.0
            
            for post in successful_automated_posts:
                auto_gen = post.get("automated_generation", {})
                provider = auto_gen.get("provider", "unknown")
                cost = auto_gen.get("cost", 0.0)
                
                # Track provider usage
                analysis["successful_providers"][provider] = \
                    analysis["successful_providers"].get(provider, 0) + 1
                
                # Track costs
                analysis["cost_analysis"]["total_cost"] += cost
                analysis["cost_analysis"]["cost_by_provider"][provider] = \
                    analysis["cost_analysis"]["cost_by_provider"].get(provider, 0) + cost
            
            # Calculate averages
            if len(successful_automated_posts) > 0:
                analysis["cost_analysis"]["avg_cost_per_post"] = \
                    analysis["cost_analysis"]["total_cost"] / len(successful_automated_posts)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing successful prompts: {e}")
            raise
    
    async def close(self):
        """Close generation service"""
        if self.generation_service:
            await self.generation_service.close()