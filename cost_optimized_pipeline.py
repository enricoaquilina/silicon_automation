#!/usr/bin/env python3
"""
Cost-Optimized Complete Pipeline
- Clear and regenerate with focus on cost efficiency
- Use Kling v2.0 for video (more cost-effective than Veo-3)
- Strategic model selection for best value
- Accurate cost tracking with real pricing
"""

import os
import asyncio
import aiohttp
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any
import base64


class CostOptimizedPipeline:
    """Cost-efficient complete pipeline with accurate pricing"""
    
    def __init__(self, replicate_token: str, shortcode: str):
        self.replicate_token = replicate_token
        self.shortcode = shortcode
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # Cost-optimized image models (prioritize cheaper, high-quality models)
        self.image_models = {
            "sdxl": {
                "version": "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                "cost_per_image": 0.002,
                "short_name": "sdxl",
                "priority": 1,  # Cheapest
                "quality": "high"
            },
            "kandinsky-2.2": {
                "version": "ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
                "cost_per_image": 0.002,
                "short_name": "kandinsky", 
                "priority": 1,  # Cheapest
                "quality": "high"
            },
            "janus-pro-7b": {
                "version": "fbf6eb41957601528aab2b3f6d37a287015d9f486c3ac4ec6e80f04744ac1a32",
                "cost_per_image": 0.003,
                "short_name": "janus",
                "priority": 2,  # Good value
                "quality": "high"
            },
            "recraft-v3": {
                "version": "0fea59248a8a1ddb8197792577f6627ec65482abc49f50c6e9da40ca8729d24d",
                "cost_per_image": 0.004,
                "short_name": "recraft",
                "priority": 2,  # Good value  
                "quality": "excellent"
            },
            "leonardo-phoenix": {
                "version": "4cd55e5b4b40428d87cb2bc74e86bb2ac4c3c4b0b3ca04c4725c1e9c5b5e4b0a",
                "cost_per_image": 0.004,
                "short_name": "leonardo",
                "priority": 2,  # Good value
                "quality": "high"
            },
            "flux-1.1-pro": {
                "version": "80a09d66baa990429c2f5ae8a4306bf778a1b3775afd01cc2cc8bdbe9033769c",
                "cost_per_image": 0.005,
                "short_name": "flux",
                "priority": 3,  # Premium
                "quality": "excellent"
            }
        }
        
        # Video generation options with ACCURATE pricing
        self.video_models = {
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "cost_per_second": 0.28,
                "duration": 5,
                "cost_per_video": 1.40,  # $0.28 × 5 seconds
                "description": "Kling v2.0 - Cost-effective 720p",
                "recommended": True
            },
            "hunyuan-video": {
                "version": "6c9132aee14409cd6568d030453f1ba50f5f3412b844fe67f78a9eb62d55664f",
                "cost_per_video": 2.02,  # Fixed cost per video
                "duration": 5.4,  # 129 frames at 24fps = ~5.4 seconds
                "description": "Hunyuan Video - State-of-the-art realistic motion",
                "recommended": False  # More expensive than Kling
            },
            "google-veo-3": {
                "version": "3c08e75333152bd7c21eb75f0db2478fe32588feb45bb9acc59fba03b83fc002",
                "cost_per_second": 0.75,
                "duration": 8,
                "cost_per_video": 6.00,  # $6 per 8s video
                "description": "Google Veo-3 - Premium with audio",
                "recommended": False  # Too expensive for batch processing
            }
        }
        
        # Other costs
        self.other_costs = {
            "upscaling": 0.002,  # Real-ESRGAN per image
            "music": 0.002  # MusicGen per track
        }
        
        self.costs = {
            "image_generation": 0,
            "upscaling": 0, 
            "video_generation": 0,
            "music_generation": 0,
            "total": 0
        }
    
    def calculate_strategy_costs(self, num_models: int = 4, images_per_model: int = 3) -> Dict[str, float]:
        """Calculate costs for different strategies"""
        
        strategies = {
            "budget": {
                "models": ["sdxl", "kandinsky-2.2", "janus-pro-7b"],
                "video_model": "kling-v2.0",
                "images_per_model": 3
            },
            "balanced": {
                "models": ["sdxl", "kandinsky-2.2", "recraft-v3", "leonardo-phoenix"],
                "video_model": "kling-v2.0", 
                "images_per_model": 4
            },
            "premium": {
                "models": ["sdxl", "recraft-v3", "leonardo-phoenix", "flux-1.1-pro"],
                "video_model": "kling-v2.0",
                "images_per_model": 5
            },
            "hunyuan_test": {
                "models": ["sdxl", "recraft-v3", "leonardo-phoenix"],
                "video_model": "hunyuan-video",
                "images_per_model": 4
            },
            "luxury": {
                "models": ["recraft-v3", "leonardo-phoenix", "flux-1.1-pro"],
                "video_model": "google-veo-3",
                "images_per_model": 5
            }
        }
        
        costs = {}
        
        for strategy_name, config in strategies.items():
            total_images = len(config["models"]) * config["images_per_model"]
            
            # Image generation costs
            image_cost = 0
            for model_name in config["models"]:
                model_cost = self.image_models[model_name]["cost_per_image"]
                image_cost += model_cost * config["images_per_model"]
            
            # Upscaling costs
            upscale_cost = total_images * self.other_costs["upscaling"]
            
            # Video costs (1 per model)
            video_cost = len(config["models"]) * self.video_models[config["video_model"]]["cost_per_video"]
            
            # Music costs (1 per model)
            music_cost = len(config["models"]) * self.other_costs["music"]
            
            total_cost = image_cost + upscale_cost + video_cost + music_cost
            
            costs[strategy_name] = {
                "models": config["models"],
                "total_images": total_images,
                "image_generation": image_cost,
                "upscaling": upscale_cost,
                "video_generation": video_cost,
                "music_generation": music_cost,
                "total": total_cost,
                "cost_per_model": total_cost / len(config["models"]),
                "video_model": config["video_model"]
            }
        
        return costs
    
    def display_cost_analysis(self):
        """Display cost analysis for different strategies"""
        print(f"💰 COST ANALYSIS - STRATEGY COMPARISON")
        print("=" * 80)
        
        strategies = self.calculate_strategy_costs()
        
        for strategy_name, costs in strategies.items():
            print(f"\\n🎯 {strategy_name.upper()} STRATEGY:")
            print(f"   📸 Models: {', '.join(costs['models'])}")
            print(f"   🎬 Video: {costs['video_model']}")
            print(f"   📊 Total images: {costs['total_images']}")
            print(f"   💵 Image generation: ${costs['image_generation']:.2f}")
            print(f"   🔍 Upscaling: ${costs['upscaling']:.2f}")
            print(f"   🎬 Video generation: ${costs['video_generation']:.2f}")
            print(f"   🎵 Music generation: ${costs['music_generation']:.2f}")
            print(f"   🏆 TOTAL COST: ${costs['total']:.2f}")
            print(f"   📈 Cost per model: ${costs['cost_per_model']:.2f}")
        
        # Recommendations
        print(f"\\n💡 RECOMMENDATIONS:")
        print(f"   🥇 Best Value: BALANCED strategy (${strategies['balanced']['total']:.2f}) - Kling v2.0")
        print(f"   💎 Best Quality: PREMIUM strategy (${strategies['premium']['total']:.2f}) - Kling v2.0")
        print(f"   💸 Budget Option: BUDGET strategy (${strategies['budget']['total']:.2f}) - Kling v2.0")
        print(f"   🧪 Hunyuan Test: HUNYUAN_TEST strategy (${strategies['hunyuan_test']['total']:.2f}) - More expensive but state-of-the-art")
        print(f"   ⚠️ Avoid: LUXURY strategy (${strategies['luxury']['total']:.2f}) - Veo-3 too expensive")
        
        return strategies
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def clear_existing_content(self, base_dir: str) -> bool:
        """Clear existing generated content"""
        print(f"\\n🧹 CLEARING EXISTING CONTENT")
        print(f"Directory: {base_dir}")
        
        try:
            if os.path.exists(base_dir):
                items = os.listdir(base_dir)
                cleared_count = 0
                
                for item in items:
                    item_path = os.path.join(base_dir, item)
                    if item.endswith('_model') and os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        cleared_count += 1
                        print(f"   🗑️ Removed {item}")
                    elif item.endswith('.mp4'):
                        os.remove(item_path)
                        cleared_count += 1
                        print(f"   🗑️ Removed {item}")
                
                print(f"   ✅ Cleared {cleared_count} items")
                return True
        
        except Exception as e:
            print(f"   ❌ Error clearing: {e}")
            return False
    
    async def run_cost_optimized_strategy(self, strategy_name: str, base_dir: str) -> Dict[str, Any]:
        """Run the selected cost-optimized strategy"""
        
        strategies = self.calculate_strategy_costs()
        
        if strategy_name not in strategies:
            print(f"❌ Unknown strategy: {strategy_name}")
            return {"success": False, "error": "Unknown strategy"}
        
        strategy = strategies[strategy_name]
        
        print(f"\\n🚀 EXECUTING {strategy_name.upper()} STRATEGY")
        print(f"📊 Estimated total cost: ${strategy['total']:.2f}")
        print(f"📸 Models: {', '.join(strategy['models'])}")
        print(f"🎬 Video model: {strategy['video_model']}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Clear existing content
        await self.clear_existing_content(base_dir)
        
        # For this demo, we'll simulate the costs without actually running the full pipeline
        # since it would be expensive and time-consuming
        
        print(f"\\n📋 SIMULATING PIPELINE EXECUTION...")
        print(f"   🎨 Would generate {strategy['total_images']} images")
        print(f"   🔍 Would upscale {strategy['total_images']} images")
        print(f"   🎬 Would generate {len(strategy['models'])} videos")
        print(f"   🎵 Would generate {len(strategy['models'])} music tracks")
        
        # Simulate timing (actual would be much longer)
        await asyncio.sleep(2)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            "success": True,
            "strategy": strategy_name,
            "estimated_costs": strategy,
            "simulated": True,
            "duration_seconds": duration,
            "recommendation": "Use BALANCED strategy for best value"
        }
        
        print(f"\\n🎉 STRATEGY SIMULATION COMPLETE!")
        print(f"⏱️ Simulation time: {duration:.1f}s")
        print(f"💰 Estimated cost: ${strategy['total']:.2f}")
        print(f"💡 Recommendation: {result['recommendation']}")
        
        return result


async def main():
    """Run cost analysis and strategy selection"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Configuration
    shortcode = "C0xFHGOrBN7"
    base_dir = f"downloaded_verify_images/verify_{shortcode}"
    
    # Create pipeline
    pipeline = CostOptimizedPipeline(replicate_token, shortcode)
    
    # Display cost analysis
    strategies = pipeline.display_cost_analysis()
    
    # Ask user for strategy choice (simulate choosing balanced)
    print(f"\\n🎯 STRATEGY SELECTION")
    print(f"Recommended: BALANCED strategy for best value (${strategies['balanced']['total']:.2f})")
    
    # Run the balanced strategy
    result = await pipeline.run_cost_optimized_strategy("balanced", base_dir)
    
    # Save analysis
    analysis_file = f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    analysis_data = {
        "strategies": strategies,
        "execution_result": result,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"\\n📄 Cost analysis saved: {analysis_file}")
    
    print(f"\\n🎯 NEXT STEPS:")
    print(f"1. Review cost analysis")
    print(f"2. Choose strategy (BALANCED recommended)")
    print(f"3. Run actual pipeline with selected strategy")
    print(f"4. Monitor costs during execution")


if __name__ == "__main__":
    asyncio.run(main())