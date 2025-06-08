#!/usr/bin/env python3
"""
Enhanced Multi-Model Pipeline with GridFS Integration
- Multiple AI models for image generation
- Model metadata embedded in files and filenames
- GridFS storage with complete metadata
- Support for different generation models
"""

import os
import asyncio
import aiohttp
import json
import base64
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib
from pymongo import MongoClient
from gridfs import GridFS
from typing import Dict, List, Any


class EnhancedMultiModelPipeline:
    """Enhanced pipeline with multiple models and GridFS storage"""
    
    # Available models configuration
    AVAILABLE_MODELS = {
        "flux-1.1-pro": {
            "version": "80a09d66baa990429c2f5ae8a4306bf778a1b3775afd01cc2cc8bdbe9033769c",
            "cost_per_image": 0.005,
            "short_name": "flux11pro",
            "description": "Flux 1.1 Pro - Advanced generation model"
        },
        "recraft-v3": {
            "version": "0fea59248a8a1ddb8197792577f6627ec65482abc49f50c6e9da40ca8729d24d",
            "cost_per_image": 0.004,
            "short_name": "recraft",
            "description": "Recraft v3 - Professional design model"
        },
        "sdxl": {
            "version": "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
            "cost_per_image": 0.002,
            "short_name": "sdxl", 
            "description": "Stable Diffusion XL"
        },
        "minimax-video": {
            "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
            "cost_per_image": 0.020,
            "short_name": "minimax",
            "description": "Minimax Video-01 - Video generation model"
        },
        "playground-v2_5": {
            "version": "a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
            "cost_per_image": 0.004,
            "short_name": "playground",
            "description": "Playground v2.5"
        },
        "kandinsky-2.2": {
            "version": "ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
            "cost_per_image": 0.002,
            "short_name": "kandinsky",
            "description": "Kandinsky 2.2 - AI Forever's text-to-image model"
        },
        "janus-pro-7b": {
            "version": "fbf6eb41957601528aab2b3f6d37a287015d9f486c3ac4ec6e80f04744ac1a32",
            "cost_per_image": 0.003,
            "short_name": "janus",
            "description": "Janus Pro 7B - DeepSeek's text-to-image generation model"
        },
        "leonardo-phoenix": {
            "version": "4cd55e5b4b40428d87cb2bc74e86bb2ac4c3c4b0b3ca04c4725c1e9c5b5e4b0a",
            "cost_per_image": 0.004,
            "short_name": "leonardo",
            "description": "Leonardo Phoenix 1.0 - Up to 5 megapixel images"
        }
    }
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        self.replicate_token = replicate_token
        self.mongodb_uri = mongodb_uri
        self.replicate_api_url = "https://api.replicate.com/v1/predictions"
        
        # MongoDB connection
        self.client = None
        self.db = None
        self.fs = None
        
    def connect_to_mongodb(self):
        """Connect to MongoDB and GridFS"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['instagram_db']
            self.fs = GridFS(self.db)
            
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB and GridFS")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("   Continuing with local storage only...")
            return False
    
    async def analyze_image_with_vlm(self, image_path: str, vlm_model: str = "blip") -> str:
        """Analyze image using specified VLM"""
        print(f"🔍 Analyzing image with {vlm_model.upper()} VLM...")
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_b64}"
            
            if vlm_model == "blip":
                payload = {
                    "version": "2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                    "input": {
                        "image": data_uri,
                        "task": "image_captioning"
                    }
                }
            elif vlm_model == "llava-13b":
                payload = {
                    "version": "80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
                    "input": {
                        "image": data_uri,
                        "prompt": "Describe this digital artwork in detail. Focus on visual composition, color scheme, artistic style, and overall aesthetic for creating similar artwork."
                    }
                }
            else:
                # Default to BLIP
                payload = {
                    "version": "2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                    "input": {
                        "image": data_uri,
                        "task": "image_captioning"
                    }
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
                        raise Exception(f"BLIP submission failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   📝 {vlm_model.upper()} prediction submitted: {prediction_id}")
                
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            description = result['output']
                            
                            # Handle different output formats
                            if isinstance(description, list):
                                # Join list of tokens/words into string
                                description = ''.join(description) if description else ""
                            elif not isinstance(description, str):
                                description = str(description)
                            
                            print(f"   ✅ {vlm_model.upper()} analysis complete: {description[:200]}...")
                            
                            # Format output consistently
                            if vlm_model == "blip":
                                return f"Caption: {description}"
                            else:
                                return f"{vlm_model.upper()}: {description}"
                        elif result['status'] == 'failed':
                            raise Exception(f"{vlm_model.upper()} analysis failed: {result.get('error')}")
                        
                        await asyncio.sleep(2)
                        
        except Exception as e:
            print(f"   ❌ {vlm_model.upper()} analysis error: {e}")
            raise e
    
    def create_enhanced_siliconsentiments_prompt(self, description: str, shortcode: str) -> str:
        """Create enhanced SiliconSentiments prompt with nature-tech fusion"""
        
        # Create safer, more abstract prompt to avoid NSFW detection
        prompt = f"""SiliconSentiments digital art transformation: Abstract interpretation of {description}

STYLE: Futuristic digital illustration, technological aesthetics, nature-inspired elements, geometric patterns, crystalline structures

ELEMENTS: Flowing data streams, holographic overlays, organic circuit patterns, luminescent accents, metallic textures, prismatic effects

COMPOSITION: Professional digital artwork, clean lines, balanced composition, high contrast, vibrant colors

COLORS: Electric blue, neon green, chrome silver, warm gold accents, deep purple highlights

MOOD: Innovative, technological, ethereal, harmonious blend of nature and technology

FORMAT: High-quality digital illustration suitable for social media"""
        
        return prompt
    
    async def _generate_single_prediction(self, prompt: str, model_name: str, model_config: dict) -> List[str]:
        """Generate a single prediction for models that don't support multiple outputs"""
        try:
            # Configure payload for single output models
            if model_name == "recraft-v3":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "size": "1024x1024",
                        "style": "digital_illustration",
                        "output_format": "jpg"
                    }
                }
            elif model_name == "janus-pro-7b":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "size": "1024x1024",
                        "guidance_scale": 4.5,
                        "num_inference_steps": 50
                    }
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
                
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            image_urls = result['output']
                            
                            # Handle different output formats
                            if isinstance(image_urls, str):
                                image_urls = [image_urls]
                            elif isinstance(image_urls, list):
                                pass
                            else:
                                image_urls = [str(image_urls)]
                            
                            return image_urls
                        elif result['status'] == 'failed':
                            raise Exception(f"{model_name} generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ {model_name} single prediction error: {e}")
            return []
    
    async def generate_with_model(self, prompt: str, model_name: str, num_outputs: int = 4) -> List[str]:
        """Generate images using specified model"""
        
        if model_name not in self.AVAILABLE_MODELS:
            raise Exception(f"Model '{model_name}' not available. Available: {list(self.AVAILABLE_MODELS.keys())}")
        
        model_config = self.AVAILABLE_MODELS[model_name]
        
        # Models that only support 1 output per prediction
        single_output_models = ["recraft-v3", "janus-pro-7b"]
        
        if model_name in single_output_models:
            print(f"🎨 Generating with {model_config['description']} ({num_outputs} separate predictions)...")
            # Make multiple separate predictions
            all_urls = []
            for i in range(num_outputs):
                urls = await self._generate_single_prediction(prompt, model_name, model_config)
                all_urls.extend(urls)
            return all_urls
        else:
            print(f"🎨 Generating with {model_config['description']} ({num_outputs} variations)...")
        
        try:
            # Model-specific payload configuration
            if model_name == "flux-1.1-pro":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "aspect_ratio": "1:1",
                        "output_format": "jpg",
                        "output_quality": 90,
                        "prompt_upsampling": True,
                        "safety_tolerance": 2
                    }
                }
            elif model_name == "recraft-v3":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "size": "1024x1024",
                        "style": "digital_illustration",
                        "output_format": "jpg"
                    }
                }
            elif model_name == "sdxl":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "width": 1024,
                        "height": 1024,
                        "num_inference_steps": 30,
                        "guidance_scale": 7.5
                    }
                }
            elif model_name == "minimax-video":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": 1,  # Video models typically output 1
                        "aspect_ratio": "16:9"
                    }
                }
            elif model_name == "playground-v2_5":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "width": 1024,
                        "height": 1024,
                        "scheduler": "K_EULER_ANCESTRAL",
                        "guidance_scale": 3,
                        "num_inference_steps": 50
                    }
                }
            elif model_name == "kandinsky-2.2":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "width": 1024,
                        "height": 1024,
                        "num_inference_steps": 50,
                        "guidance_scale": 4
                    }
                }
            elif model_name == "janus-pro-7b":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "size": "1024x1024",
                        "guidance_scale": 4.5,
                        "num_inference_steps": 50
                    }
                }
            elif model_name == "leonardo-phoenix":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": prompt,
                        "num_outputs": num_outputs,
                        "width": 1024,
                        "height": 1024,
                        "guidance_scale": 7,
                        "num_inference_steps": 30,
                        "high_resolution": True
                    }
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
                    print(f"   🎯 {model_name} generation submitted: {prediction_id}")
                
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            image_urls = result['output']
                            
                            # Handle different output formats
                            if isinstance(image_urls, str):
                                # Single URL returned as string
                                image_urls = [image_urls]
                            elif isinstance(image_urls, list):
                                # List of URLs (expected format)
                                pass
                            else:
                                # Unexpected format
                                image_urls = [str(image_urls)]
                            
                            print(f"   ✅ {model_name} generation complete - {len(image_urls)} variations")
                            return image_urls
                        elif result['status'] == 'failed':
                            raise Exception(f"{model_name} generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ {model_name} generation error: {e}")
            raise e
    
    def add_metadata_to_image(self, image_path: str, metadata: Dict[str, Any]) -> str:
        """Add metadata to image file"""
        try:
            # Load image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create metadata string
                metadata_json = json.dumps(metadata, indent=2)
                
                # Add metadata as comment (works for JPEG)
                exif_dict = img.getexif()
                exif_dict[0x9286] = metadata_json  # UserComment tag
                
                # Save with metadata
                img.save(image_path, "JPEG", exif=exif_dict, quality=90)
                
            print(f"   📋 Added metadata to {os.path.basename(image_path)}")
            return image_path
            
        except Exception as e:
            print(f"   ⚠️ Could not add metadata to {image_path}: {e}")
            return image_path
    
    async def save_to_gridfs(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """Save file to GridFS with metadata"""
        if not self.fs:
            print("   ⚠️ GridFS not connected, skipping GridFS storage")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                file_id = self.fs.put(
                    f,
                    filename=os.path.basename(file_path),
                    metadata=metadata,
                    content_type="image/jpeg"
                )
            
            print(f"   💾 Saved to GridFS: {file_id}")
            return str(file_id)
            
        except Exception as e:
            print(f"   ❌ GridFS save error: {e}")
            return None
    
    async def download_and_save_images(self, urls: List[str], shortcode: str, model_name: str, 
                                     output_dir: str, original_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Download images with model name in filename and complete metadata"""
        
        model_config = self.AVAILABLE_MODELS[model_name]
        short_name = model_config["short_name"]
        
        print(f"💾 Downloading {len(urls)} {model_name} variations...")
        
        downloaded_files = []
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                try:
                    # Enhanced filename with model name
                    filename = f"{shortcode}_{short_name}_v{i}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Download image
                    async with session.get(url) as response:
                        if response.status == 200:
                            with open(filepath, 'wb') as f:
                                f.write(await response.read())
                            
                            size = os.path.getsize(filepath)
                            
                            # Create comprehensive metadata
                            generation_metadata = {
                                "siliconsentiments_generation": {
                                    "model_name": model_name,
                                    "model_version": model_config["version"],
                                    "model_description": model_config["description"],
                                    "generation_cost": model_config["cost_per_image"],
                                    "variation_number": i,
                                    "generation_timestamp": datetime.now().isoformat(),
                                    "source_shortcode": shortcode,
                                    "source_url": f"https://instagram.com/p/{shortcode}/",
                                    "brand": "SiliconSentiments",
                                    "pipeline_version": "enhanced_multi_model_v1.0"
                                },
                                "original_image": original_metadata,
                                "technical_info": {
                                    "file_size_bytes": size,
                                    "format": "JPEG",
                                    "generated_url": url
                                }
                            }
                            
                            # Add metadata to image file
                            self.add_metadata_to_image(filepath, generation_metadata)
                            
                            # Save to GridFS with metadata
                            gridfs_id = await self.save_to_gridfs(filepath, generation_metadata)
                            
                            file_info = {
                                'filename': filename,
                                'filepath': filepath,
                                'url': url,
                                'size_bytes': size,
                                'variation': i,
                                'model_name': model_name,
                                'model_short_name': short_name,
                                'gridfs_id': gridfs_id,
                                'metadata': generation_metadata
                            }
                            
                            downloaded_files.append(file_info)
                            print(f"   ✅ Downloaded: {filename} ({size:,} bytes)")
                            
                        else:
                            print(f"   ❌ Failed to download variation {i}: {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Download error for variation {i}: {e}")
                    continue
        
        print(f"   🎉 Successfully downloaded {len(downloaded_files)}/{len(urls)} variations")
        return downloaded_files
    
    async def process_image_with_models(self, image_path: str, shortcode: str, output_dir: str, 
                                      models: List[str] = None, vlm_model: str = "blip") -> Dict[str, Any]:
        """Process image with multiple models"""
        
        if models is None:
            models = ["flux-1.1-pro"]  # Default to Flux 1.1 Pro
        
        print(f"🚀 ENHANCED MULTI-MODEL PIPELINE")
        print(f"Input: {image_path}")
        print(f"Shortcode: {shortcode}")
        print(f"Models: {', '.join(models)}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Connect to MongoDB
            mongodb_connected = self.connect_to_mongodb()
            
            # Step 1: Analyze with VLM
            description = await self.analyze_image_with_vlm(image_path, vlm_model)
            print(f"📝 VLM Description: {description}")
            
            # Step 2: Create enhanced prompt
            prompt = self.create_enhanced_siliconsentiments_prompt(description, shortcode)
            print(f"🎯 Enhanced SiliconSentiments prompt created")
            
            # Get original image metadata
            original_metadata = {
                "source_path": image_path,
                "source_shortcode": shortcode,
                "vlm_description": description,
                "file_size": os.path.getsize(image_path) if os.path.exists(image_path) else 0
            }
            
            # Step 3: Generate with each model
            all_results = {}
            total_cost = 0
            
            for model_name in models:
                model_config = self.AVAILABLE_MODELS[model_name]
                print(f"\n🎨 Processing with {model_name}...")
                
                try:
                    # Generate images
                    generated_urls = await self.generate_with_model(prompt, model_name, num_outputs=4)
                    
                    # Download and save with metadata
                    downloaded_files = await self.download_and_save_images(
                        generated_urls, shortcode, model_name, output_dir, original_metadata
                    )
                    
                    model_cost = len(downloaded_files) * model_config["cost_per_image"]
                    total_cost += model_cost
                    
                    all_results[model_name] = {
                        "success": True,
                        "generated_files": downloaded_files,
                        "cost": model_cost,
                        "variations_count": len(downloaded_files)
                    }
                    
                    print(f"   ✅ {model_name}: {len(downloaded_files)} variations (${model_cost:.3f})")
                    
                except Exception as e:
                    print(f"   ❌ {model_name} failed: {e}")
                    all_results[model_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Final results
            successful_models = [m for m, r in all_results.items() if r.get("success")]
            total_variations = sum(r.get("variations_count", 0) for r in all_results.values() if r.get("success"))
            
            result = {
                'success': len(successful_models) > 0,
                'shortcode': shortcode,
                'original_image': image_path,
                'vlm_description': description,
                'enhanced_prompt': prompt,
                'models_processed': models,
                'successful_models': successful_models,
                'model_results': all_results,
                'total_variations_generated': total_variations,
                'total_cost': total_cost,
                'mongodb_connected': mongodb_connected,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n🎉 PIPELINE COMPLETE!")
            print(f"✅ Successful models: {', '.join(successful_models)}")
            print(f"✅ Total variations: {total_variations}")
            print(f"⏱️ Duration: {duration:.1f}s")
            print(f"💰 Total cost: ${total_cost:.3f}")
            print(f"💾 GridFS connected: {'Yes' if mongodb_connected else 'No'}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n❌ PIPELINE FAILED: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }


async def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python enhanced_multi_model_pipeline.py <image_path> <shortcode> [models]")
        print("Available models: flux-1.1-pro, recraft-v3, sdxl, minimax-video, playground-v2_5, kandinsky-2.2, janus-pro-7b, leonardo-phoenix")
        print("Available VLMs: blip, llava-13b")
        print("Example: python enhanced_multi_model_pipeline.py image.jpg C0xFHGOrBN7 flux-1.1-pro,janus-pro-7b llava-13b")
        return
    
    image_path = sys.argv[1]
    shortcode = sys.argv[2]
    
    # Parse models and VLM
    if len(sys.argv) > 3:
        models = [m.strip() for m in sys.argv[3].split(',')]
    else:
        models = ["flux-1.1-pro"]
    
    # Parse VLM (optional 4th argument)
    vlm_model = "blip"  # default
    if len(sys.argv) > 4:
        vlm_model = sys.argv[4].strip()
    
    # Validate models
    available_models = list(EnhancedMultiModelPipeline.AVAILABLE_MODELS.keys())
    invalid_models = [m for m in models if m not in available_models]
    if invalid_models:
        print(f"❌ Invalid models: {invalid_models}")
        print(f"Available models: {available_models}")
        return
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Setup output directory
    output_dir = os.path.dirname(image_path)
    
    # Run enhanced pipeline
    pipeline = EnhancedMultiModelPipeline(replicate_token)
    result = await pipeline.process_image_with_models(image_path, shortcode, output_dir, models, vlm_model)
    
    # Save result
    report_path = os.path.join(output_dir, f'enhanced_multi_model_result_{shortcode}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Result saved: {report_path}")
    
    if result.get('success'):
        print(f"\n🎉 SUCCESS! Enhanced multi-model pipeline complete!")
        print(f"✅ Models: {', '.join(result.get('successful_models', []))}")
        print(f"✅ Total variations: {result.get('total_variations_generated', 0)}")
        print(f"💰 Cost: ${result.get('total_cost', 0):.3f}")
        print(f"🚀 Ready for production deployment!")


if __name__ == "__main__":
    asyncio.run(main())