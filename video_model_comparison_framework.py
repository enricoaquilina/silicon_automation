#!/usr/bin/env python3
"""
Video Model Comparison Framework
- Test multiple state-of-the-art video generation models
- Compare quality, cost, speed, and reliability
- Generate comprehensive analysis reports
- Support for Veo-3, Kling, Wan2.1, Leonardo Motion, Pixverse, etc.
"""

import os
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from multimedia_content_pipeline import MultimediaContentPipeline


class VideoModelComparator:
    """Framework for comparing multiple video generation models"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.replicate_token = replicate_token
        self.mongodb_uri = mongodb_uri
        self.replicate_api_url = "https://api.replicate.com/v1/predictions"
        
        # State-of-the-art video models to test
        self.video_models = {
            # Tier 1: Premium Models
            "kling-v2.0": {
                "version": "kwaivgi/kling-v2.0:latest",
                "description": "Kling v2.0 - 5s/10s videos in 720p",
                "features": ["text-to-video", "image-to-video", "720p", "5s/10s"],
                "tier": "premium",
                "estimated_cost": 0.05  # per 5s video
            },
            "minimax-video-01": {
                "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
                "description": "Minimax Video-01 (Hailuo) - 6s videos",
                "features": ["text-to-video", "image-to-video", "6s"],
                "tier": "premium", 
                "estimated_cost": 0.06
            },
            
            # Tier 2: Specialized Models
            "wan2.1-i2v": {
                "version": "ae5bc519ee414f255f66c7ac22062e01bbbd6050c04f888d002d5ee0dc087a0c",
                "description": "Wan2.1 Image-to-Video specialist - 480p",
                "features": ["image-to-video", "480p", "81-frames"],
                "tier": "specialized",
                "estimated_cost": 0.062  # ~5.1s @ $0.0122/s
            },
            
            # Tier 3: Current Working (Baseline)
            "animate-diff": {
                "version": "lucataco/animate-diff:latest",
                "description": "AnimateDiff - Current working model",
                "features": ["text-to-video", "reliable", "proven"],
                "tier": "baseline",
                "estimated_cost": 0.0115
            }
        }
    
    async def test_video_model(self, model_key: str, image_path: str, prompt: str,
                              duration: int = 5) -> Dict[str, Any]:
        """Test a specific video model with standardized inputs"""
        
        model_config = self.video_models.get(model_key)
        if not model_config:
            return {"success": False, "error": f"Model {model_key} not found"}
        
        print(f"🎬 Testing {model_key}: {model_config['description']}")
        
        start_time = time.time()
        
        try:
            # Enhanced video prompt for SiliconSentiments
            enhanced_prompt = f"""SiliconSentiments digital art: {prompt}
            
STYLE: Futuristic cybernetic aesthetic, neural network visualization, technological beauty
MOVEMENT: Gentle geometric transformations, flowing data particles, pulsing circuit elements
CAMERA: Smooth cinematic movement, subtle zoom, professional composition
QUALITY: High-definition, crisp details, professional video production
MOOD: Contemplative, innovative, artistic, brand-consistent SiliconSentiments
EFFECTS: Glowing accents, holographic overlays, depth of field, particle systems"""

            # Model-specific API call
            if model_key == "kling-v2.0":
                result = await self._test_kling_v2(image_path, enhanced_prompt, duration)
            elif model_key == "minimax-video-01":
                result = await self._test_minimax_video_01(image_path, enhanced_prompt, duration)
            elif model_key == "wan2.1-i2v":
                result = await self._test_wan21_i2v(image_path, enhanced_prompt, duration)
            elif model_key == "animate-diff":
                result = await self.generate_video_from_image(image_path, prompt, duration, "animate-diff")
            else:
                result = {"success": False, "error": f"Model {model_key} not implemented"}
            
            generation_time = time.time() - start_time
            
            # Add performance metrics
            if result.get("success"):
                result.update({
                    "model_key": model_key,
                    "model_config": model_config,
                    "generation_time": generation_time,
                    "prompt_used": enhanced_prompt,
                    "test_timestamp": datetime.now().isoformat()
                })
            
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            print(f"   ❌ {model_key} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_key": model_key,
                "generation_time": generation_time,
                "test_timestamp": datetime.now().isoformat()
            }
    
    async def _test_kling_v2(self, image_path: str, prompt: str, duration: int) -> Dict[str, Any]:
        """Test Kling v2.0 model"""
        return await self._generate_with_replicate_model(
            model_version="kwaivgi/kling-v2.0:latest",
            inputs={
                "prompt": prompt,
                "image": self._image_to_data_uri(image_path),
                "duration": duration,
                "aspect_ratio": "1:1"
            },
            model_name="kling-v2.0"
        )
    
    async def _test_minimax_video_01(self, image_path: str, prompt: str, duration: int) -> Dict[str, Any]:
        """Test Minimax Video-01 model"""
        return await self._generate_with_replicate_model(
            model_version="c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
            inputs={
                "prompt": prompt,
                "first_frame_image": self._image_to_data_uri(image_path),
                "prompt_optimizer": True
            },
            model_name="minimax-video-01"
        )
    
    async def _test_wan21_i2v(self, image_path: str, prompt: str, duration: int) -> Dict[str, Any]:
        """Test Wan2.1 Image-to-Video model"""
        return await self._generate_with_replicate_model(
            model_version="ae5bc519ee414f255f66c7ac22062e01bbbd6050c04f888d002d5ee0dc087a0c",
            inputs={
                "image": self._image_to_data_uri(image_path),
                "prompt": prompt,
                "num_frames": 81,
                "sample_steps": 30,
                "fps": 16,
                "sample_guide_scale": 5,
                "sample_shift": 3,
                "fast_mode": "balanced"
            },
            model_name="wan2.1-i2v"
        )
    
    def _image_to_data_uri(self, image_path: str) -> str:
        """Convert image file to data URI for API"""
        import base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def _generate_with_replicate_model(self, model_version: str, inputs: Dict[str, Any], 
                                           model_name: str) -> Dict[str, Any]:
        """Generic function to generate video with any Replicate model"""
        try:
            payload = {
                "version": model_version,
                "input": inputs
            }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise Exception(f"{model_name} submission failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   🎯 {model_name} prediction submitted: {prediction_id}")
                
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            video_urls = result['output']
                            
                            # Handle different output formats
                            if isinstance(video_urls, str):
                                video_urls = [video_urls]
                            elif isinstance(video_urls, list):
                                pass
                            else:
                                video_urls = [str(video_urls)]
                            
                            print(f"   ✅ {model_name} generation complete")
                            return {
                                "success": True,
                                "video_urls": video_urls,
                                "prediction_id": prediction_id,
                                "model_name": model_name
                            }
                        elif result['status'] == 'failed':
                            raise Exception(f"{model_name} generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ {model_name} generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name
            }
    
    async def run_comprehensive_comparison(self, test_images: List[str], 
                                         output_dir: str) -> Dict[str, Any]:
        """Run comprehensive comparison across all models and test images"""
        
        print(f"🚀 COMPREHENSIVE VIDEO MODEL COMPARISON")
        print(f"Test Images: {len(test_images)}")
        print(f"Models: {len(self.video_models)}")
        print(f"Total Tests: {len(test_images) * len(self.video_models)}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        comparison_results = {
            "test_metadata": {
                "start_time": start_time.isoformat(),
                "test_images": test_images,
                "models_tested": list(self.video_models.keys()),
                "total_tests": len(test_images) * len(self.video_models)
            },
            "model_results": {},
            "image_results": {},
            "summary": {}
        }
        
        total_cost = 0
        successful_tests = 0
        
        # Test each image with each model
        for i, image_path in enumerate(test_images, 1):
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            print(f"\\n📸 Testing Image {i}/{len(test_images)}: {image_name}")
            
            image_results = {}
            
            # Generate description for consistent prompting
            prompt = f"Transform this digital artwork into a dynamic SiliconSentiments branded animation"
            
            for model_key in self.video_models.keys():
                print(f"   🎬 Model: {model_key}")
                
                result = await self.test_video_model(model_key, image_path, prompt)
                
                if result.get("success"):
                    successful_tests += 1
                    total_cost += self.video_models[model_key]["estimated_cost"]
                    print(f"      ✅ Success - {result.get('generation_time', 0):.1f}s")
                else:
                    print(f"      ❌ Failed - {result.get('error', 'Unknown error')}")
                
                image_results[model_key] = result
                
                # Initialize model results if not exists
                if model_key not in comparison_results["model_results"]:
                    comparison_results["model_results"][model_key] = []
                
                comparison_results["model_results"][model_key].append(result)
            
            comparison_results["image_results"][image_name] = image_results
        
        # Generate summary statistics
        duration = (datetime.now() - start_time).total_seconds()
        
        model_summary = {}
        for model_key, model_results in comparison_results["model_results"].items():
            successes = [r for r in model_results if r.get("success")]
            failures = [r for r in model_results if not r.get("success")]
            
            if successes:
                avg_time = sum(r.get("generation_time", 0) for r in successes) / len(successes)
            else:
                avg_time = 0
                
            model_summary[model_key] = {
                "total_tests": len(model_results),
                "successes": len(successes),
                "failures": len(failures),
                "success_rate": len(successes) / len(model_results) if model_results else 0,
                "avg_generation_time": avg_time,
                "estimated_cost_per_video": self.video_models[model_key]["estimated_cost"],
                "total_estimated_cost": len(successes) * self.video_models[model_key]["estimated_cost"]
            }
        
        comparison_results["summary"] = {
            "total_tests": len(test_images) * len(self.video_models),
            "successful_tests": successful_tests,
            "success_rate": successful_tests / (len(test_images) * len(self.video_models)),
            "total_duration": duration,
            "estimated_total_cost": total_cost,
            "model_summary": model_summary,
            "end_time": datetime.now().isoformat()
        }
        
        # Save comprehensive results
        results_file = os.path.join(output_dir, f"video_model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)
        
        # Generate comparison report
        await self._generate_comparison_report(comparison_results, output_dir)
        
        print(f"\\n🎉 COMPARISON COMPLETE!")
        print(f"✅ Success Rate: {comparison_results['summary']['success_rate']:.1%}")
        print(f"⏱️ Duration: {duration/60:.1f} minutes")
        print(f"💰 Estimated Cost: ${total_cost:.2f}")
        print(f"📄 Results: {results_file}")
        
        return comparison_results
    
    async def _generate_comparison_report(self, results: Dict[str, Any], output_dir: str) -> str:
        """Generate markdown comparison report"""
        
        report_file = os.path.join(output_dir, f"VIDEO_MODEL_COMPARISON_REPORT.md")
        
        with open(report_file, 'w') as f:
            f.write("# Video Model Comparison Report\\n\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            # Summary
            summary = results["summary"]
            f.write("## Executive Summary\\n\\n")
            f.write(f"- **Total Tests**: {summary['total_tests']}\\n")
            f.write(f"- **Success Rate**: {summary['success_rate']:.1%}\\n")
            f.write(f"- **Duration**: {summary['total_duration']/60:.1f} minutes\\n")
            f.write(f"- **Estimated Cost**: ${summary['estimated_total_cost']:.2f}\\n\\n")
            
            # Model Performance Table
            f.write("## Model Performance Comparison\\n\\n")
            f.write("| Model | Success Rate | Avg Time | Cost/Video | Total Cost | Tier |\\n")
            f.write("|-------|-------------|----------|------------|------------|------|\\n")
            
            for model_key, model_stats in summary["model_summary"].items():
                model_config = self.video_models[model_key]
                f.write(f"| {model_key} | {model_stats['success_rate']:.1%} | "
                       f"{model_stats['avg_generation_time']:.1f}s | "
                       f"${model_stats['estimated_cost_per_video']:.3f} | "
                       f"${model_stats['total_estimated_cost']:.2f} | "
                       f"{model_config['tier']} |\\n")
            
            f.write("\\n")
            
            # Detailed Results by Model
            f.write("## Detailed Model Analysis\\n\\n")
            
            for model_key, model_config in self.video_models.items():
                model_stats = summary["model_summary"][model_key]
                f.write(f"### {model_key.upper()}\\n")
                f.write(f"**Description**: {model_config['description']}\\n")
                f.write(f"**Features**: {', '.join(model_config['features'])}\\n")
                f.write(f"**Performance**:\\n")
                f.write(f"- Success Rate: {model_stats['success_rate']:.1%}\\n")
                f.write(f"- Average Generation Time: {model_stats['avg_generation_time']:.1f}s\\n")
                f.write(f"- Cost per Video: ${model_stats['estimated_cost_per_video']:.3f}\\n")
                f.write(f"- Total Cost: ${model_stats['total_estimated_cost']:.2f}\\n\\n")
            
            # Recommendations
            f.write("## Recommendations\\n\\n")
            
            # Find best performing models
            working_models = {k: v for k, v in summary["model_summary"].items() 
                            if v["success_rate"] > 0}
            
            if working_models:
                best_quality = max(working_models.items(), key=lambda x: x[1]["success_rate"])
                best_cost = min(working_models.items(), key=lambda x: x[1]["estimated_cost_per_video"])
                best_speed = min(working_models.items(), key=lambda x: x[1]["avg_generation_time"])
                
                f.write(f"- **Best Reliability**: {best_quality[0]} ({best_quality[1]['success_rate']:.1%} success)\\n")
                f.write(f"- **Most Cost-Effective**: {best_cost[0]} (${best_cost[1]['estimated_cost_per_video']:.3f}/video)\\n")
                f.write(f"- **Fastest Generation**: {best_speed[0]} ({best_speed[1]['avg_generation_time']:.1f}s average)\\n")
            
            f.write("\\n---\\n")
            f.write("*Generated by SiliconSentiments Video Model Comparison Framework*\\n")
        
        print(f"   📄 Report generated: {report_file}")
        return report_file


async def main():
    """Run video model comparison"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_model_comparison_framework.py <test_images_directory>")
        print("Example: python video_model_comparison_framework.py downloaded_verify_images/verify_C0xFHGOrBN7/recraft_model/upscaled_images/")
        return
    
    test_dir = sys.argv[1]
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find test images
    test_images = []
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.endswith(('_upscaled.jpg', '.jpg', '.png')):
                test_images.append(os.path.join(test_dir, file))
    
    if not test_images:
        print(f"❌ No test images found in {test_dir}")
        return
    
    # Limit to first 3 images for initial testing
    test_images = test_images[:3]
    
    # Setup output directory
    output_dir = os.path.join(os.path.dirname(test_dir), "video_model_comparison_results")
    
    # Run comparison
    comparator = VideoModelComparator(replicate_token)
    results = await comparator.run_comprehensive_comparison(test_images, output_dir)
    
    if results.get("summary"):
        print(f"\\n🏆 COMPARISON COMPLETE!")
        print(f"📊 Check results in: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())