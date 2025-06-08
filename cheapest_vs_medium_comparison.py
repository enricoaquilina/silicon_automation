#!/usr/bin/env python3
"""
Cheapest vs Medium Video Model Comparison
- Test ultra-cheap models vs proven medium-cost models
- Create mix-and-match strategy for Instagram database
- Optimize cost vs quality for different content types
"""

import os
import asyncio
import aiohttp
import base64
import json
from datetime import datetime
from typing import Dict, List, Any


class CheapestVsMediumComparison:
    """Compare cheapest vs medium-priced video models for strategic deployment"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # Categorized models by cost tier
        self.video_models = {
            # ULTRA-CHEAP TIER (Under $0.10)
            "luma-ray-flash-2": {
                "version": "95ab790a8dd6d5a0a3527cb6c9a0b22a8b3f2ce8fef23ae60d5dc6a1ad8ba6af",  # Need to verify
                "cost_per_video": 0.022,  # ~$0.0043 p50 × 5s
                "description": "Luma Ray Flash 2 - Ultra cheap 720p",
                "tier": "ultra-cheap",
                "features": ["image-to-video", "720p", "5s", "ultra-cheap"],
                "quality_tier": "unknown",
                "use_cases": ["bulk_processing", "testing", "budget_content"]
            },
            "leonardo-motion-2": {
                "version": "3a2633c4fc40d3b76c0cf31c9b859ff3f6a9f524972365c3c868f99ba90ee70d",
                "cost_per_video": 0.025,  # ~$0.0051 p50 × 5s
                "description": "Leonardo Motion 2.0 - Ultra cheap 480p",
                "tier": "ultra-cheap", 
                "features": ["image-to-video", "480p", "5s", "style-options"],
                "quality_tier": "unknown",
                "use_cases": ["bulk_processing", "testing", "style_variations"]
            },
            
            # MEDIUM TIER ($1-2)
            "kling-v2": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "cost_per_video": 1.40,
                "description": "Kling v2.0 - Proven reliable 720p",
                "tier": "medium",
                "features": ["image-to-video", "720p", "5s", "reliable"],
                "quality_tier": "proven-good",
                "use_cases": ["premium_content", "important_posts", "proven_quality"]
            },
            "hunyuan-video": {
                "version": "6c9132aee14409cd6568d030453f1ba50f5f3412b844fe67f78a9eb62d55664f",
                "cost_per_video": 2.02,
                "description": "Hunyuan Video - State-of-the-art motion",
                "tier": "medium",
                "features": ["text-to-video", "realistic-motion", "5.4s", "state-of-the-art"],
                "quality_tier": "premium",
                "use_cases": ["hero_content", "showcase_posts", "maximum_quality"]
            }
        }
        
        self.total_cost = 0
        self.comparison_results = {}
    
    def display_model_tiers(self):
        """Display models organized by cost tiers"""
        print(f"💰 VIDEO MODEL COST TIERS")
        print("=" * 80)
        
        ultra_cheap = {k: v for k, v in self.video_models.items() if v["tier"] == "ultra-cheap"}
        medium = {k: v for k, v in self.video_models.items() if v["tier"] == "medium"}
        
        print(f"\\n🎯 ULTRA-CHEAP TIER (Under $0.10)")
        for model_key, config in ultra_cheap.items():
            features = ", ".join(config["features"])
            print(f"   💸 {model_key}: ${config['cost_per_video']:.3f} - {features}")
        
        print(f"\\n🎯 MEDIUM TIER ($1-2)")
        for model_key, config in medium.items():
            features = ", ".join(config["features"])
            print(f"   💰 {model_key}: ${config['cost_per_video']:.2f} - {features}")
        
        # Cost comparison
        cheapest = min(self.video_models.values(), key=lambda x: x["cost_per_video"])
        most_expensive = max(self.video_models.values(), key=lambda x: x["cost_per_video"])
        cost_ratio = most_expensive["cost_per_video"] / cheapest["cost_per_video"]
        
        print(f"\\n📊 COST ANALYSIS:")
        print(f"   💸 Cheapest: ${cheapest['cost_per_video']:.3f}")
        print(f"   💎 Most expensive: ${most_expensive['cost_per_video']:.2f}")
        print(f"   📈 Cost ratio: {cost_ratio:.0f}x difference")
        
        return ultra_cheap, medium
    
    def calculate_instagram_db_strategies(self):
        """Calculate costs for different Instagram database strategies"""
        print(f"\\n🗄️ INSTAGRAM DATABASE DEPLOYMENT STRATEGIES")
        print("=" * 60)
        
        # Assume we have different types of content in our 2,639 posts
        content_distribution = {
            "hero_posts": 50,        # Top performing, important posts
            "premium_content": 200,  # High-quality posts
            "standard_content": 800, # Regular posts
            "bulk_content": 1589     # Remaining posts
        }
        
        total_posts = sum(content_distribution.values())
        
        strategies = {
            "all_ultra_cheap": {
                "description": "Use cheapest model for everything",
                "allocation": {
                    "luma-ray-flash-2": total_posts
                },
                "use_case": "Maximum cost savings"
            },
            "all_medium": {
                "description": "Use proven reliable model for everything", 
                "allocation": {
                    "kling-v2": total_posts
                },
                "use_case": "Consistent proven quality"
            },
            "mixed_strategic": {
                "description": "Strategic mix based on content importance",
                "allocation": {
                    "hunyuan-video": content_distribution["hero_posts"],      # Best for hero content
                    "kling-v2": content_distribution["premium_content"],      # Reliable for premium
                    "leonardo-motion-2": content_distribution["standard_content"], # Cheap for standard
                    "luma-ray-flash-2": content_distribution["bulk_content"]  # Cheapest for bulk
                },
                "use_case": "Optimal cost vs quality balance"
            },
            "two_tier": {
                "description": "Simple two-tier approach",
                "allocation": {
                    "kling-v2": content_distribution["hero_posts"] + content_distribution["premium_content"],
                    "luma-ray-flash-2": content_distribution["standard_content"] + content_distribution["bulk_content"]
                },
                "use_case": "Simple management, good savings"
            }
        }
        
        # Calculate costs for each strategy
        strategy_costs = {}
        
        for strategy_name, strategy in strategies.items():
            total_cost = 0
            cost_breakdown = {}
            
            for model_key, post_count in strategy["allocation"].items():
                model_cost = self.video_models[model_key]["cost_per_video"]
                cost = post_count * model_cost
                total_cost += cost
                cost_breakdown[model_key] = {
                    "posts": post_count,
                    "cost_per_video": model_cost,
                    "total_cost": cost
                }
            
            strategy_costs[strategy_name] = {
                "total_cost": total_cost,
                "cost_breakdown": cost_breakdown,
                "description": strategy["description"],
                "use_case": strategy["use_case"],
                "cost_per_post": total_cost / total_posts
            }
        
        # Display results
        for strategy_name, data in strategy_costs.items():
            print(f"\\n🎯 {strategy_name.upper().replace('_', ' ')} STRATEGY")
            print(f"   📝 {data['description']}")
            print(f"   🎯 Use case: {data['use_case']}")
            print(f"   💰 Total cost: ${data['total_cost']:.2f}")
            print(f"   📊 Cost per post: ${data['cost_per_post']:.3f}")
            
            for model_key, breakdown in data['cost_breakdown'].items():
                print(f"      • {model_key}: {breakdown['posts']} posts × ${breakdown['cost_per_video']:.3f} = ${breakdown['total_cost']:.2f}")
        
        # Savings analysis
        baseline_cost = strategy_costs["all_medium"]["total_cost"]
        
        print(f"\\n💡 SAVINGS ANALYSIS (vs All Medium Strategy):")
        for strategy_name, data in strategy_costs.items():
            if strategy_name != "all_medium":
                savings = baseline_cost - data["total_cost"]
                savings_percent = (savings / baseline_cost) * 100
                print(f"   💸 {strategy_name}: Save ${savings:.2f} ({savings_percent:.1f}%)")
        
        return strategy_costs
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def test_luma_ray_flash_2(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Luma Ray Flash 2 - ultra cheap 720p"""
        print(f"\\n💸 Testing Luma Ray Flash 2 (ultra-cheap)...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["luma-ray-flash-2"]["version"],
                "input": {
                    "prompt": prompt,
                    "start_image_url": image_uri,
                    "duration": 5,
                    "resolution": "720p"
                }
            }
            
            return await self._run_prediction("luma-ray-flash-2", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "luma-ray-flash-2"}
    
    async def test_leonardo_motion_2(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Leonardo Motion 2.0 - ultra cheap 480p"""
        print(f"\\n💸 Testing Leonardo Motion 2.0 (ultra-cheap)...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["leonardo-motion-2"]["version"],
                "input": {
                    "prompt": prompt,
                    "image": image_uri,
                    "aspect_ratio": "1:1",
                    "prompt_enhancement": True,
                    "frame_interpolation": True
                }
            }
            
            return await self._run_prediction("leonardo-motion-2", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "leonardo-motion-2"}
    
    async def test_kling_v2(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Kling v2.0 - proven medium cost"""
        print(f"\\n💰 Testing Kling v2.0 (proven medium)...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["kling-v2"]["version"],
                "input": {
                    "prompt": prompt,
                    "start_image": image_uri,
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            }
            
            return await self._run_prediction("kling-v2", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "kling-v2"}
    
    async def _run_prediction(self, model_key: str, payload: dict) -> Dict[str, Any]:
        """Generic prediction runner"""
        
        model_config = self.video_models[model_key]
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Submit prediction
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        print(f"   ❌ {model_key} submission failed: {response.status}")
                        return {"success": False, "error": f"Submission failed: {response.status} - {error_text}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ {model_key} prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed % 30 < 3:  # Status every 30s
                            print(f"   📊 {model_key}: {status} ({elapsed:.1f}s)")
                        
                        if status == 'succeeded':
                            video_output = result['output']
                            
                            if isinstance(video_output, list):
                                video_url = video_output[0] if video_output else None
                            elif isinstance(video_output, str):
                                video_url = video_output
                            else:
                                video_url = str(video_output) if video_output else None
                            
                            if video_url:
                                # Download video
                                timestamp = datetime.now().strftime('%H%M%S')
                                output_filename = f"tier_compare_{model_key}_{timestamp}.mp4"
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(output_filename, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                        cost = model_config["cost_per_video"]
                                        self.total_cost += cost
                                        
                                        print(f"   🎉 {model_key} SUCCESS!")
                                        print(f"   📁 File: {output_filename}")
                                        print(f"   📊 {size_mb:.1f}MB, {elapsed:.1f}s, ${cost:.3f}")
                                        
                                        return {
                                            "success": True,
                                            "model": model_key,
                                            "file": output_filename,
                                            "size_mb": size_mb,
                                            "generation_time": elapsed,
                                            "cost": cost,
                                            "tier": model_config["tier"],
                                            "quality_tier": model_config["quality_tier"],
                                            "features": model_config["features"]
                                        }
                        
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            print(f"   ❌ {model_key} failed: {error}")
                            return {"success": False, "error": error, "model": model_key}
                        
                        if elapsed > 600:  # 10 minute timeout
                            return {"success": False, "error": "Timeout", "model": model_key}
                        
                        await asyncio.sleep(8)
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {"success": False, "error": str(e), "model": model_key, "time": elapsed}
    
    async def run_tier_comparison(self, test_image: str) -> Dict[str, Any]:
        """Run comparison between cheapest and medium tiers"""
        
        print(f"🚀 CHEAPEST vs MEDIUM TIER COMPARISON")
        print(f"Test image: {os.path.basename(test_image)}")
        print("=" * 70)
        
        # Display cost tiers
        ultra_cheap, medium = self.display_model_tiers()
        
        # Calculate Instagram DB strategies
        strategy_costs = self.calculate_instagram_db_strategies()
        
        start_time = datetime.now()
        
        # Optimized prompt for all models
        prompt = "SiliconSentiments digital artwork with gentle cinematic movement and technological aesthetic"
        
        print(f"\\n🎬 TESTING REPRESENTATIVE MODELS...")
        print(f"📝 Prompt: '{prompt}'")
        
        # Test one from each tier for direct comparison
        test_models = [
            ("luma-ray-flash-2", self.test_luma_ray_flash_2(test_image, prompt)),     # Ultra-cheap
            ("leonardo-motion-2", self.test_leonardo_motion_2(test_image, prompt)),   # Ultra-cheap backup  
            ("kling-v2", self.test_kling_v2(test_image, prompt))                     # Proven medium
        ]
        
        results = {}
        
        # Run tests sequentially
        for model_name, test_coro in test_models:
            result = await test_coro
            results[model_name] = result
            
            # Wait between tests
            await asyncio.sleep(5)
        
        duration = (datetime.now() - start_time).total_seconds()
        successful = [r for r in results.values() if r.get("success")]
        
        # Analysis
        comparison_analysis = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_image": test_image,
                "prompt": prompt,
                "duration_minutes": duration / 60
            },
            "tier_results": results,
            "strategy_costs": strategy_costs,
            "recommendations": self._generate_recommendations(results, strategy_costs)
        }
        
        print(f"\\n🎉 TIER COMPARISON COMPLETE!")
        print(f"✅ Successful: {len(successful)}/{len(results)} models")
        print(f"💰 Test cost: ${self.total_cost:.3f}")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        
        if successful:
            print(f"\\n🏆 TIER COMPARISON RESULTS:")
            
            # Group by tier
            ultra_cheap_results = [r for r in successful if r.get("tier") == "ultra-cheap"]
            medium_results = [r for r in successful if r.get("tier") == "medium"]
            
            if ultra_cheap_results:
                print(f"\\n   💸 ULTRA-CHEAP TIER:")
                for result in ultra_cheap_results:
                    print(f"      🎥 {result['model']}: ${result['cost']:.3f}, {result['size_mb']:.1f}MB, {result['generation_time']:.1f}s")
            
            if medium_results:
                print(f"\\n   💰 MEDIUM TIER:")
                for result in medium_results:
                    print(f"      🎥 {result['model']}: ${result['cost']:.2f}, {result['size_mb']:.1f}MB, {result['generation_time']:.1f}s")
        
        # Display recommendations
        print(f"\\n💡 STRATEGIC RECOMMENDATIONS:")
        for rec in comparison_analysis["recommendations"]:
            print(f"   {rec}")
        
        # Save comprehensive analysis
        analysis_file = f"cheapest_vs_medium_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(comparison_analysis, f, indent=2, default=str)
        
        print(f"\\n📄 Complete analysis saved: {analysis_file}")
        
        return comparison_analysis
    
    def _generate_recommendations(self, results: Dict, strategy_costs: Dict) -> List[str]:
        """Generate strategic recommendations based on results"""
        recommendations = []
        
        successful = [r for r in results.values() if r.get("success")]
        
        if len(successful) >= 2:
            # Find cheapest working model
            cheapest = min(successful, key=lambda x: x["cost"])
            most_expensive = max(successful, key=lambda x: x["cost"])
            
            recommendations.append(f"🥇 Best value: {cheapest['model']} at ${cheapest['cost']:.3f} per video")
            recommendations.append(f"💎 Premium option: {most_expensive['model']} at ${most_expensive['cost']:.2f} per video")
            
            # Cost savings
            if cheapest["cost"] < 0.10:
                savings_vs_medium = ((1.40 - cheapest["cost"]) / 1.40) * 100
                recommendations.append(f"💸 Ultra-cheap model saves {savings_vs_medium:.1f}% vs medium-tier models")
        
        # Strategy recommendations
        mixed_strategy_cost = strategy_costs.get("mixed_strategic", {}).get("total_cost", 0)
        all_cheap_cost = strategy_costs.get("all_ultra_cheap", {}).get("total_cost", 0)
        
        if mixed_strategy_cost and all_cheap_cost:
            recommendations.append(f"🎯 Mixed strategy costs ${mixed_strategy_cost:.2f} for 2,639 posts")
            recommendations.append(f"💸 All ultra-cheap costs ${all_cheap_cost:.2f} for 2,639 posts")
            recommendations.append(f"🚀 Test ultra-cheap models first, fall back to proven models if needed")
        
        return recommendations


async def main():
    """Run cheapest vs medium tier comparison"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find test image
    import glob
    images = glob.glob("downloaded_verify_images/**/*upscaled.jpg", recursive=True)
    
    if not images:
        print("❌ No upscaled test images found")
        return
    
    test_image = images[0]
    print(f"✅ Using test image: {os.path.basename(test_image)}")
    
    # Run comparison
    comparator = CheapestVsMediumComparison(replicate_token)
    analysis = await comparator.run_tier_comparison(test_image)
    
    print(f"\\n🚀 READY FOR STRATEGIC DEPLOYMENT!")
    print(f"✅ Use analysis to choose optimal mix-and-match strategy")
    print(f"💡 Deploy ultra-cheap models for bulk content, medium for premium")


if __name__ == "__main__":
    asyncio.run(main())