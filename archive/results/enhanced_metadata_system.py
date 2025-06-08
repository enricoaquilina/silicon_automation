#!/usr/bin/env python3
"""
Enhanced Metadata Management System

Prepares comprehensive metadata structure for web app integration:
- VLM description extraction and storage
- Multi-model prompt generation
- Unified metadata schema
- Instagram shortcode integration
- Description/prompt versioning
"""

import os
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

class VLMDescriptionExtractor:
    """Extract descriptions from images using Vision Language Models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
    
    async def extract_description_blip(self, image_url: str) -> Dict[str, Any]:
        """Extract description using BLIP model"""
        try:
            import replicate
            
            output = replicate.run(
                "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                input={
                    "image": image_url,
                    "task": "image_captioning"
                }
            )
            
            return {
                "success": True,
                "description": output if isinstance(output, str) else str(output),
                "model": "salesforce/blip",
                "timestamp": datetime.now(timezone.utc),
                "source_url": image_url
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": "salesforce/blip",
                "timestamp": datetime.now(timezone.utc)
            }
    
    async def extract_description_llava(self, image_url: str) -> Dict[str, Any]:
        """Extract detailed description using LLaVA model"""
        try:
            import replicate
            
            output = replicate.run(
                "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddda3e32fd8a0e75dc39d8a4191bb742157fb",
                input={
                    "image": image_url,
                    "prompt": "Describe this image in detail. Focus on: 1) Visual composition and layout, 2) Color scheme and lighting, 3) Artistic style and technique, 4) Subject matter and themes, 5) Overall mood and aesthetic. Be specific and descriptive for use in image generation prompts."
                }
            )
            
            return {
                "success": True,
                "description": output if isinstance(output, str) else str(output),
                "model": "yorickvp/llava-13b",
                "timestamp": datetime.now(timezone.utc),
                "source_url": image_url,
                "analysis_type": "detailed_artistic"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": "yorickvp/llava-13b",
                "timestamp": datetime.now(timezone.utc)
            }

class MultiModelPromptManager:
    """Generate and manage prompts for different image generation models"""
    
    def __init__(self):
        self.model_configs = {
            "flux-schnell": {
                "style": "concise",
                "max_length": 200,
                "cost_per_image": 0.003,
                "emphasis": ["fast", "efficient", "clean"],
                "supports_negative": False,
                "typical_inference_steps": 4
            },
            "flux-dev": {
                "style": "detailed",
                "max_length": 300,
                "cost_per_image": 0.055,
                "emphasis": ["quality", "artistic", "detailed"],
                "supports_negative": False,
                "typical_inference_steps": 50
            },
            "flux-pro": {
                "style": "professional",
                "max_length": 350,
                "cost_per_image": 0.055,
                "emphasis": ["professional", "commercial", "polished"],
                "supports_negative": False,
                "typical_inference_steps": 25
            },
            "sdxl": {
                "style": "structured",
                "max_length": 250,
                "cost_per_image": 0.0039,
                "emphasis": ["photorealistic", "detailed", "structured"],
                "supports_negative": True,
                "typical_inference_steps": 50
            },
            "midjourney-v6": {
                "style": "artistic",
                "max_length": 300,
                "cost_per_image": 0.0125,  # Estimated
                "emphasis": ["creative", "stylized", "atmospheric"],
                "supports_negative": False,
                "special_parameters": ["--v 6", "--style", "--chaos", "--ar"]
            },
            "dalle-3": {
                "style": "natural",
                "max_length": 400,
                "cost_per_image": 0.040,  # Standard quality
                "emphasis": ["natural", "coherent", "safe"],
                "supports_negative": False,
                "supports_revision": True
            }
        }
        
        # SiliconSentiments brand elements
        self.brand_elements = {
            "core_themes": [
                "neural network consciousness",
                "quantum computing interfaces",
                "cybernetic organism design",
                "artificial intelligence emergence",
                "blockchain reality visualization",
                "algorithmic pattern synthesis",
                "digital consciousness evolution",
                "holographic data architecture",
                "synthetic biology networks",
                "augmented perception layers"
            ],
            "visual_styles": [
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
            "quality_modifiers": [
                "8K ultra-resolution clarity",
                "photorealistic rendering quality",
                "volumetric lighting effects",
                "atmospheric depth layering",
                "sharp geometric precision",
                "professional studio composition",
                "cinematic color grading",
                "award-winning photography"
            ]
        }
    
    def generate_model_specific_prompts(self, description: str, models: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """Generate optimized prompts for multiple models"""
        if models is None:
            models = ["flux-schnell", "flux-dev", "sdxl", "midjourney-v6"]
        
        import random
        
        prompts = {}
        
        for model in models:
            if model not in self.model_configs:
                continue
                
            config = self.model_configs[model]
            
            # Select brand elements based on model style
            theme = random.choice(self.brand_elements["core_themes"])
            styles = random.sample(self.brand_elements["visual_styles"], 3)
            colors = random.choice(self.brand_elements["color_palettes"])
            quality = random.choice(self.brand_elements["quality_modifiers"])
            
            # Build base prompt
            if "inspired by" in description or "post about" in description:
                base_prompt = f"SiliconSentiments {theme} inspired by {description[:150]}"
            else:
                base_prompt = f"SiliconSentiments {theme}: {description[:120]}"
            
            # Model-specific adjustments
            if model == "flux-schnell":
                prompt = f"{base_prompt}, {styles[0]}, {colors}, clean composition"
                
            elif model == "flux-dev":
                prompt = f"{base_prompt}, {', '.join(styles)}, {colors}, {quality}, professional lighting"
                
            elif model == "flux-pro":
                prompt = f"{base_prompt}, {', '.join(styles)}, {colors}, {quality}, commercial grade, studio photography"
                
            elif model == "sdxl":
                prompt = f"Photorealistic {base_prompt}, {', '.join(styles[:2])}, {colors}, {quality}"
                negative_prompt = "blurry, low quality, distorted, amateur, oversaturated, ugly, deformed"
                
            elif model == "midjourney-v6":
                prompt = f"{base_prompt}, {', '.join(styles)}, {colors}, atmospheric, --v 6 --style raw --ar 1:1"
                
            elif model == "dalle-3":
                prompt = f"{base_prompt}. Style: {styles[0]} with {colors}. High quality digital art with {quality.lower()}."
            
            # Create prompt object
            prompt_obj = {
                "positive_prompt": prompt,
                "model": model,
                "estimated_cost": config["cost_per_image"],
                "style": config["style"],
                "emphasis": config["emphasis"],
                "generated_at": datetime.now(timezone.utc),
                "brand_elements_used": {
                    "theme": theme,
                    "styles": styles,
                    "colors": colors,
                    "quality": quality
                }
            }
            
            # Add model-specific fields
            if config.get("supports_negative") and model == "sdxl":
                prompt_obj["negative_prompt"] = negative_prompt
            
            if "special_parameters" in config:
                prompt_obj["special_parameters"] = config["special_parameters"]
            
            if "typical_inference_steps" in config:
                prompt_obj["inference_steps"] = config["typical_inference_steps"]
            
            prompts[model] = prompt_obj
        
        return prompts

class EnhancedMetadataManager:
    """Manage comprehensive metadata for web app integration"""
    
    def __init__(self, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.fs = None
        
        self.vlm_extractor = None
        self.prompt_manager = MultiModelPromptManager()
    
    def connect(self, replicate_token: str = None):
        """Connect to MongoDB and initialize VLM if token provided"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB")
            
            if replicate_token:
                self.vlm_extractor = VLMDescriptionExtractor(replicate_token)
                print("✅ VLM extractor initialized")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def enhance_post_metadata(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance post with comprehensive metadata for web app"""
        
        enhanced_post = {
            **post_data,
            "_id": str(post_data["_id"]) if "_id" in post_data else None,
            
            # Instagram integration
            "instagram_url": f"https://instagram.com/p/{post_data.get('shortcode', '')}" if post_data.get('shortcode') else None,
            "siliconsentiments_url": f"https://instagram.com/siliconsentiments_art/p/{post_data.get('shortcode', '')}" if post_data.get('shortcode') else None,
            
            # Metadata enhancement
            "metadata_version": "3.0",
            "web_app_ready": True,
            "enhanced_at": datetime.now(timezone.utc),
            
            # Analysis status
            "analysis_status": {
                "description_extracted": False,
                "prompts_generated": False,
                "images_generated": False,
                "ready_for_generation": False
            },
            
            # VLM analysis placeholder
            "vlm_analysis": {
                "descriptions": [],
                "last_analyzed": None,
                "analysis_models_used": []
            },
            
            # Multi-model prompts placeholder
            "generation_prompts": {
                "models": {},
                "last_generated": None,
                "prompt_version": "3.0"
            },
            
            # Generation tracking
            "generation_history": [],
            "current_best_generation": None,
            "total_generation_cost": 0.0
        }
        
        # Check if post has existing images
        if "image_ref" in post_data:
            try:
                image_doc = self.db.post_images.find_one({"_id": post_data["image_ref"]})
                if image_doc:
                    enhanced_post["analysis_status"]["images_generated"] = True
                    enhanced_post["current_image_data"] = {
                        "image_ref_id": str(image_doc["_id"]),
                        "created_at": image_doc.get("created_at"),
                        "provider": image_doc.get("automation_info", {}).get("provider"),
                        "model": image_doc.get("automation_info", {}).get("model"),
                        "cost": image_doc.get("automation_info", {}).get("cost", 0)
                    }
                    enhanced_post["total_generation_cost"] = enhanced_post["current_image_data"]["cost"]
            except Exception as e:
                print(f"⚠️  Error enhancing image data: {e}")
        
        return enhanced_post
    
    async def extract_and_store_description(self, post_id: str, image_url: str, vlm_model: str = "blip") -> Dict[str, Any]:
        """Extract description using VLM and store in database"""
        
        if not self.vlm_extractor:
            return {"success": False, "error": "VLM extractor not initialized"}
        
        try:
            # Extract description
            if vlm_model == "llava":
                result = await self.vlm_extractor.extract_description_llava(image_url)
            else:
                result = await self.vlm_extractor.extract_description_blip(image_url)
            
            if result["success"]:
                # Store in post's VLM analysis
                update_data = {
                    "$push": {
                        "vlm_analysis.descriptions": result,
                        "vlm_analysis.analysis_models_used": vlm_model
                    },
                    "$set": {
                        "vlm_analysis.last_analyzed": datetime.now(timezone.utc),
                        "analysis_status.description_extracted": True
                    }
                }
                
                self.db.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    update_data
                )
                
                print(f"✅ Description extracted and stored for post {post_id}")
                
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_and_store_prompts(self, post_id: str, description: str, models: List[str] = None) -> Dict[str, Any]:
        """Generate multi-model prompts and store in database"""
        
        try:
            # Generate prompts
            prompts = self.prompt_manager.generate_model_specific_prompts(description, models)
            
            # Store in post's generation prompts
            update_data = {
                "$set": {
                    "generation_prompts.models": prompts,
                    "generation_prompts.last_generated": datetime.now(timezone.utc),
                    "generation_prompts.source_description": description,
                    "analysis_status.prompts_generated": True,
                    "analysis_status.ready_for_generation": True
                }
            }
            
            self.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                update_data
            )
            
            print(f"✅ Prompts generated and stored for post {post_id}")
            
            return {
                "success": True,
                "prompts": prompts,
                "models_count": len(prompts),
                "total_estimated_cost": sum(p["estimated_cost"] for p in prompts.values())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_posts_for_web_app(self, limit: int = 50, filter_type: str = "all") -> List[Dict[str, Any]]:
        """Get posts with enhanced metadata for web app display"""
        
        # Build query based on filter
        query = {}
        if filter_type == "with_images":
            query["image_ref"] = {"$exists": True}
        elif filter_type == "without_images":
            query["image_ref"] = {"$exists": False}
        elif filter_type == "ready_to_publish":
            query["instagram_status"] = "ready_to_publish"
        elif filter_type == "need_analysis":
            query = {
                "$or": [
                    {"vlm_analysis": {"$exists": False}},
                    {"analysis_status.description_extracted": False}
                ]
            }
        
        # Get posts
        posts = list(self.db.posts.find(query).sort("_id", -1).limit(limit))
        
        # Enhance each post
        enhanced_posts = []
        for post in posts:
            enhanced_post = self.enhance_post_metadata(post)
            enhanced_posts.append(enhanced_post)
        
        return enhanced_posts
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics for web app dashboard"""
        
        try:
            analytics = {
                "posts": {
                    "total": self.db.posts.count_documents({}),
                    "with_images": self.db.posts.count_documents({"image_ref": {"$exists": True}}),
                    "ready_to_publish": self.db.posts.count_documents({"instagram_status": "ready_to_publish"}),
                    "with_vlm_analysis": self.db.posts.count_documents({"vlm_analysis.descriptions": {"$ne": []}}),
                    "with_prompts": self.db.posts.count_documents({"generation_prompts.models": {"$ne": {}}})
                },
                "generations": {
                    "total": self.db.post_images.count_documents({}),
                    "automated": self.db.post_images.count_documents({"automation_info": {"$exists": True}}),
                    "midjourney": self.db.post_images.count_documents({"automation_info": {"$exists": False}}),
                },
                "costs": {
                    "total_spent": 0.0,
                    "average_per_image": 0.0,
                    "by_provider": {}
                },
                "models_used": {},
                "generated_at": datetime.now(timezone.utc)
            }
            
            # Calculate derived stats
            analytics["posts"]["without_images"] = analytics["posts"]["total"] - analytics["posts"]["with_images"]
            analytics["posts"]["completion_percentage"] = round(
                (analytics["posts"]["with_images"] / analytics["posts"]["total"]) * 100, 1
            ) if analytics["posts"]["total"] > 0 else 0
            
            # Calculate costs from automation_info
            automated_gens = list(self.db.post_images.find(
                {"automation_info.cost": {"$exists": True}},
                {"automation_info.cost": 1, "automation_info.provider": 1, "automation_info.model": 1}
            ))
            
            total_cost = sum(gen["automation_info"]["cost"] for gen in automated_gens if "cost" in gen["automation_info"])
            analytics["costs"]["total_spent"] = total_cost
            analytics["costs"]["average_per_image"] = total_cost / len(automated_gens) if automated_gens else 0
            
            # Provider breakdown
            provider_costs = {}
            model_counts = {}
            for gen in automated_gens:
                provider = gen["automation_info"].get("provider", "unknown")
                model = gen["automation_info"].get("model", "unknown")
                cost = gen["automation_info"].get("cost", 0)
                
                if provider not in provider_costs:
                    provider_costs[provider] = 0
                provider_costs[provider] += cost
                
                model_key = f"{provider}_{model}"
                if model_key not in model_counts:
                    model_counts[model_key] = 0
                model_counts[model_key] += 1
            
            analytics["costs"]["by_provider"] = provider_costs
            analytics["models_used"] = model_counts
            
            return analytics
            
        except Exception as e:
            return {"error": str(e)}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Example usage and demo
async def demo_enhanced_metadata():
    """Demonstrate enhanced metadata system"""
    
    print("🔬 ENHANCED METADATA SYSTEM DEMO")
    print("=" * 60)
    
    # Get API token
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize system
    metadata_manager = EnhancedMetadataManager()
    
    try:
        # Connect
        if not metadata_manager.connect(replicate_token):
            return
        
        # Get analytics
        print("📊 CURRENT ANALYTICS:")
        analytics = metadata_manager.get_analytics_data()
        for category, data in analytics.items():
            if isinstance(data, dict):
                print(f"   {category.title()}:")
                for key, value in data.items():
                    print(f"      {key}: {value}")
            else:
                print(f"   {category}: {data}")
        
        # Get posts ready for web app
        print(f"\n📝 POSTS SAMPLE (Enhanced for Web App):")
        posts = metadata_manager.get_posts_for_web_app(limit=3)
        
        for i, post in enumerate(posts, 1):
            print(f"\n   Post {i}: {post.get('shortcode', 'Unknown')}")
            print(f"      Instagram URL: {post.get('instagram_url', 'N/A')}")
            print(f"      Has images: {post['analysis_status']['images_generated']}")
            print(f"      Description extracted: {post['analysis_status']['description_extracted']}")
            print(f"      Prompts generated: {post['analysis_status']['prompts_generated']}")
            print(f"      Ready for generation: {post['analysis_status']['ready_for_generation']}")
        
        # Demo VLM analysis (if there's an existing image)
        post_with_image = next((p for p in posts if p["analysis_status"]["images_generated"]), None)
        if post_with_image:
            print(f"\n🔍 VLM ANALYSIS DEMO:")
            print(f"   Post: {post_with_image['shortcode']}")
            print("   (VLM analysis would extract description from existing image)")
            
            # Demo prompt generation
            print(f"\n🎨 PROMPT GENERATION DEMO:")
            sample_description = "Futuristic digital art with cybernetic elements and neon lighting"
            prompts = metadata_manager.prompt_manager.generate_model_specific_prompts(sample_description)
            
            for model, prompt_data in prompts.items():
                print(f"   {model}:")
                print(f"      Prompt: {prompt_data['positive_prompt'][:100]}...")
                print(f"      Cost: ${prompt_data['estimated_cost']:.4f}")
                if "negative_prompt" in prompt_data:
                    print(f"      Negative: {prompt_data['negative_prompt'][:50]}...")
        
        print(f"\n✅ Enhanced metadata system ready for web app integration!")
        print(f"   - VLM description extraction ready")
        print(f"   - Multi-model prompt generation ready") 
        print(f"   - Instagram shortcode integration ready")
        print(f"   - Comprehensive analytics ready")
        
    finally:
        metadata_manager.close()

if __name__ == "__main__":
    asyncio.run(demo_enhanced_metadata())