#!/usr/bin/env python3
"""
SiliconSentiments Image Generation Web App

A comprehensive Flask web application for managing Instagram posts,
image generation, and metadata with VLM integration.
"""

import os
import asyncio
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import aiohttp
import io

# Import our existing systems
import sys
sys.path.append('..')
from image_generation_system import SiliconSentimentsImageSystem

app = Flask(__name__)
CORS(app)

# Global configuration
MONGODB_URI = "mongodb://192.168.0.22:27017/"
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
GEMINI_TOKEN = os.getenv("GEMINI_API_KEY")

# Global database connections
client = MongoClient(MONGODB_URI)
db = client['instagram_db']
fs = GridFS(db)

class VLMDescriptionExtractor:
    """Extract descriptions from images using Vision Language Models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
    
    async def extract_description_replicate_blip(self, image_url: str) -> str:
        """Extract description using Replicate BLIP model"""
        try:
            import replicate
            
            output = replicate.run(
                "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                input={
                    "image": image_url,
                    "task": "image_captioning",
                    "question": "Describe this image in detail, focusing on visual elements, style, colors, and artistic techniques."
                }
            )
            
            return output if isinstance(output, str) else str(output)
            
        except Exception as e:
            return f"Description extraction failed: {str(e)}"
    
    async def extract_description_replicate_llava(self, image_url: str) -> str:
        """Extract description using Replicate LLaVA model"""
        try:
            import replicate
            
            output = replicate.run(
                "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddda3e32fd8a0e75dc39d8a4191bb742157fb",
                input={
                    "image": image_url,
                    "prompt": "Describe this image in detail. Focus on: 1) Visual composition and layout, 2) Color scheme and lighting, 3) Artistic style and technique, 4) Subject matter and themes, 5) Overall mood and aesthetic. Be specific and descriptive."
                }
            )
            
            return output if isinstance(output, str) else str(output)
            
        except Exception as e:
            return f"LLaVA description extraction failed: {str(e)}"

class MultiModelPromptGenerator:
    """Generate optimized prompts for different image generation models"""
    
    def __init__(self):
        self.model_configs = {
            "flux-schnell": {
                "style": "concise",
                "max_length": 200,
                "emphasis": ["technical", "clean", "modern"],
                "negative_prompts": False
            },
            "flux-dev": {
                "style": "detailed", 
                "max_length": 300,
                "emphasis": ["artistic", "detailed", "professional"],
                "negative_prompts": False
            },
            "sdxl": {
                "style": "structured",
                "max_length": 250,
                "emphasis": ["photorealistic", "high-quality", "detailed"],
                "negative_prompts": True
            },
            "midjourney": {
                "style": "artistic",
                "max_length": 300,
                "emphasis": ["creative", "stylized", "atmospheric"],
                "negative_prompts": False
            }
        }
    
    def generate_model_specific_prompt(self, description: str, model: str, brand_theme: str = "siliconsentiments") -> Dict[str, str]:
        """Generate model-specific prompts"""
        config = self.model_configs.get(model, self.model_configs["flux-schnell"])
        
        # Base SiliconSentiments elements
        tech_elements = [
            "neural network visualization", "quantum computing interface",
            "cybernetic design", "digital consciousness", "algorithmic patterns"
        ]
        
        style_elements = [
            "clean minimalist", "geometric precision", "neon accents",
            "metallic surfaces", "holographic effects", "gradient transitions"
        ]
        
        # Model-specific adjustments
        if model == "flux-schnell":
            prompt = f"SiliconSentiments tech art: {description[:100]}, {tech_elements[0]}, {style_elements[0]}, high contrast, clean composition"
        
        elif model == "flux-dev":
            prompt = f"Advanced SiliconSentiments artwork inspired by {description[:150]}, incorporating {tech_elements[1]} and {style_elements[1]}, professional studio lighting, 8K detail"
        
        elif model == "sdxl":
            prompt = f"Photorealistic SiliconSentiments digital art: {description[:120]}, featuring {tech_elements[2]} with {style_elements[2]}, ultra-detailed, professional photography"
        
        elif model == "midjourney":
            prompt = f"SiliconSentiments artistic vision: {description[:150]} reimagined as {tech_elements[3]}, with {style_elements[3]}, atmospheric lighting, --v 6 --style raw"
        
        result = {"positive_prompt": prompt}
        
        # Add negative prompt for models that support it
        if config["negative_prompts"]:
            result["negative_prompt"] = "blurry, low quality, distorted, amateur, oversaturated, ugly"
        
        return result

# Initialize global components
vlm_extractor = VLMDescriptionExtractor(REPLICATE_TOKEN) if REPLICATE_TOKEN else None
prompt_generator = MultiModelPromptGenerator()
image_system = SiliconSentimentsImageSystem(REPLICATE_TOKEN, GEMINI_TOKEN) if REPLICATE_TOKEN else None

@app.route('/')
def dashboard():
    """Main dashboard showing statistics and recent activity"""
    try:
        # Get statistics
        total_posts = db.posts.count_documents({})
        posts_with_images = db.posts.count_documents({"image_ref": {"$exists": True}})
        posts_needing_images = total_posts - posts_with_images
        ready_to_publish = db.posts.count_documents({"instagram_status": "ready_to_publish"})
        
        # Get recent generations
        recent_generations = list(db.post_images.find({
            "automation_info": {"$exists": True}
        }).sort("_id", -1).limit(6))
        
        # Calculate costs
        total_cost = 0
        for gen in recent_generations:
            total_cost += gen.get("automation_info", {}).get("cost", 0)
        
        stats = {
            "total_posts": total_posts,
            "posts_with_images": posts_with_images,
            "posts_needing_images": posts_needing_images,
            "ready_to_publish": ready_to_publish,
            "completion_percentage": round((posts_with_images / total_posts) * 100, 1) if total_posts > 0 else 0,
            "recent_cost": total_cost,
            "recent_generations": len(recent_generations)
        }
        
        return render_template('dashboard.html', stats=stats, recent_generations=recent_generations)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/posts')
def posts_list():
    """List posts with pagination and filtering"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        filter_type = request.args.get('filter', 'all')
        
        # Build query
        query = {}
        if filter_type == 'with_images':
            query["image_ref"] = {"$exists": True}
        elif filter_type == 'without_images':
            query["image_ref"] = {"$exists": False}
        elif filter_type == 'ready_to_publish':
            query["instagram_status"] = "ready_to_publish"
        
        # Get posts with pagination
        skip = (page - 1) * per_page
        posts = list(db.posts.find(query).sort("_id", -1).skip(skip).limit(per_page))
        total_posts = db.posts.count_documents(query)
        
        # Enrich posts with image data
        for post in posts:
            post["_id"] = str(post["_id"])
            if "image_ref" in post:
                image_doc = db.post_images.find_one({"_id": post["image_ref"]})
                if image_doc:
                    post["image_data"] = image_doc
        
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total_posts,
            "pages": (total_posts + per_page - 1) // per_page,
            "has_prev": page > 1,
            "has_next": page < ((total_posts + per_page - 1) // per_page)
        }
        
        return render_template('posts_list.html', posts=posts, pagination=pagination, filter_type=filter_type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/post/<shortcode>')
def post_detail(shortcode):
    """Detailed view of a single post with all generations"""
    try:
        # Get post
        post = db.posts.find_one({"shortcode": shortcode})
        if not post:
            return "Post not found", 404
        
        post["_id"] = str(post["_id"])
        
        # Get image generations if they exist
        image_data = None
        if "image_ref" in post:
            image_data = db.post_images.find_one({"_id": post["image_ref"]})
            if image_data:
                image_data["_id"] = str(image_data["_id"])
        
        # Get all generations for this post (there might be multiple)
        all_generations = list(db.post_images.find({"post_id": post["_id"]}))
        for gen in all_generations:
            gen["_id"] = str(gen["_id"])
        
        return render_template('post_detail.html', 
                             post=post, 
                             image_data=image_data, 
                             all_generations=all_generations,
                             instagram_url=f"https://instagram.com/p/{shortcode}")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate/<shortcode>')
def generate_page(shortcode):
    """Page for generating new images for a post"""
    try:
        post = db.posts.find_one({"shortcode": shortcode})
        if not post:
            return "Post not found", 404
        
        post["_id"] = str(post["_id"])
        
        # Get existing descriptions if any
        existing_descriptions = []
        if "image_ref" in post:
            image_doc = db.post_images.find_one({"_id": post["image_ref"]})
            if image_doc and "images" in image_doc:
                for img in image_doc["images"]:
                    if "midjourney_generations" in img:
                        for gen in img["midjourney_generations"]:
                            if "options" in gen and "original_description" in gen["options"]:
                                existing_descriptions.append(gen["options"]["original_description"])
        
        return render_template('generate.html', 
                             post=post,
                             existing_descriptions=existing_descriptions,
                             available_models=list(prompt_generator.model_configs.keys()))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract_description', methods=['POST'])
async def extract_description():
    """Extract description from image URL using VLM"""
    try:
        data = request.json
        image_url = data.get('image_url')
        model = data.get('model', 'blip')
        
        if not image_url:
            return jsonify({"error": "image_url required"}), 400
        
        if not vlm_extractor:
            return jsonify({"error": "VLM not available - check REPLICATE_API_TOKEN"}), 500
        
        if model == 'llava':
            description = await vlm_extractor.extract_description_replicate_llava(image_url)
        else:
            description = await vlm_extractor.extract_description_replicate_blip(image_url)
        
        return jsonify({
            "description": description,
            "model_used": model,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_prompts', methods=['POST'])
def generate_prompts():
    """Generate model-specific prompts from description"""
    try:
        data = request.json
        description = data.get('description', '')
        models = data.get('models', ['flux-schnell'])
        
        if not description:
            return jsonify({"error": "description required"}), 400
        
        prompts = {}
        for model in models:
            prompts[model] = prompt_generator.generate_model_specific_prompt(description, model)
        
        return jsonify({
            "prompts": prompts,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_image', methods=['POST'])
async def generate_image():
    """Generate image using specified model and prompt"""
    try:
        data = request.json
        post_id = data.get('post_id')
        provider = data.get('provider', 'replicate')
        model = data.get('model', 'flux-schnell')
        custom_description = data.get('description', '')
        
        if not post_id:
            return jsonify({"error": "post_id required"}), 400
        
        if not image_system:
            return jsonify({"error": "Image generation system not available"}), 500
        
        # Connect to database
        image_system.connect_to_mongodb()
        
        # Generate image
        result = await image_system.analyze_and_generate(
            post_id=post_id,
            provider=provider,
            model=model,
            custom_description=custom_description
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/image/<file_id>')
def serve_image(file_id):
    """Serve image from GridFS"""
    try:
        grid_file = fs.get(ObjectId(file_id))
        return send_file(
            io.BytesIO(grid_file.read()),
            mimetype='image/png',
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/batch_generate', methods=['POST'])
async def batch_generate():
    """Generate images for multiple posts"""
    try:
        data = request.json
        batch_size = data.get('batch_size', 5)
        provider = data.get('provider', 'replicate')
        model = data.get('model', 'flux-schnell')
        
        if not image_system:
            return jsonify({"error": "Image generation system not available"}), 500
        
        # Connect to database
        image_system.connect_to_mongodb()
        
        # Get posts that need images
        posts = list(db.posts.find({
            "image_ref": {"$exists": False},
            "instagram_status": {"$in": ["no_status", None]}
        }).limit(batch_size))
        
        if not posts:
            return jsonify({"error": "No posts need images"}), 400
        
        results = []
        for post in posts:
            post_id = str(post["_id"])
            result = await image_system.analyze_and_generate(
                post_id=post_id,
                provider=provider,
                model=model
            )
            results.append({
                "post_id": post_id,
                "shortcode": post.get("shortcode", "unknown"),
                "result": result
            })
        
        successful = [r for r in results if r["result"].get("success")]
        failed = [r for r in results if not r["result"].get("success")]
        
        return jsonify({
            "batch_size": len(posts),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    try:
        stats = {
            "total_posts": db.posts.count_documents({}),
            "posts_with_images": db.posts.count_documents({"image_ref": {"$exists": True}}),
            "ready_to_publish": db.posts.count_documents({"instagram_status": "ready_to_publish"}),
            "total_generations": db.post_images.count_documents({}),
            "automated_generations": db.post_images.count_documents({"automation_info": {"$exists": True}})
        }
        
        stats["posts_needing_images"] = stats["total_posts"] - stats["posts_with_images"]
        stats["completion_percentage"] = round((stats["posts_with_images"] / stats["total_posts"]) * 100, 1) if stats["total_posts"] > 0 else 0
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)