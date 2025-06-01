#!/usr/bin/env python3
"""
MCP Server for SiliconSentiments MongoDB Analysis

This MCP server provides tools to analyze Instagram data stored in MongoDB,
identify missing images, and integrate with the image generation system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import gridfs

# Import additional modules
from image_generation_tools import ImageGenerationIntegration
from instagram_analysis import InstagramAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_mongodb_server")


class SiliconSentimentsMongoDB:
    """MongoDB interface for SiliconSentiments data analysis"""
    
    def __init__(self, mongodb_uri: str, db_name: str = "silicon_sentiments"):
        """
        Initialize MongoDB connection
        
        Args:
            mongodb_uri: MongoDB connection URI (e.g., mongodb://pi_ip:27017/)
            db_name: Database name
        """
        self.mongodb_uri = mongodb_uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.fs = None
        
    async def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.db_name]
            self.fs = GridFS(self.db)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {self.mongodb_uri}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "database_name": self.db_name,
                "collections": {},
                "total_documents": 0,
                "total_size_mb": 0
            }
            
            # Get collection statistics
            for collection_name in self.db.list_collection_names():
                collection = self.db[collection_name]
                count = collection.count_documents({})
                stats["collections"][collection_name] = {
                    "document_count": count,
                    "indexes": list(collection.list_indexes())
                }
                stats["total_documents"] += count
            
            # Get database size
            db_stats = self.db.command("dbStats")
            stats["total_size_mb"] = round(db_stats.get("dataSize", 0) / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise
    
    async def analyze_posts_collection(self) -> Dict[str, Any]:
        """Analyze posts collection for missing images and patterns"""
        try:
            posts_collection = self.db.posts
            post_images_collection = self.db.post_images
            
            # Get all posts
            posts = list(posts_collection.find({}))
            
            analysis = {
                "total_posts": len(posts),
                "posts_with_images": 0,
                "posts_without_images": 0,
                "published_posts": 0,
                "unpublished_posts": 0,
                "instagram_statuses": {},
                "missing_image_posts": [],
                "generation_statistics": {
                    "total_generations": 0,
                    "successful_generations": 0,
                    "failed_generations": 0,
                    "models_used": {}
                }
            }
            
            for post in posts:
                # Check Instagram status
                instagram_status = post.get("instagram_status", "unknown")
                analysis["instagram_statuses"][instagram_status] = \
                    analysis["instagram_statuses"].get(instagram_status, 0) + 1
                
                if instagram_status == "published":
                    analysis["published_posts"] += 1
                else:
                    analysis["unpublished_posts"] += 1
                
                # Check for image reference
                image_ref = post.get("image_ref")
                if image_ref:
                    # Get image document
                    image_doc = post_images_collection.find_one({"_id": image_ref})
                    if image_doc and image_doc.get("images"):
                        analysis["posts_with_images"] += 1
                        
                        # Analyze generations
                        for image in image_doc["images"]:
                            generations = image.get("midjourney_generations", [])
                            analysis["generation_statistics"]["total_generations"] += len(generations)
                            
                            for gen in generations:
                                if gen.get("midjourney_image_id"):
                                    analysis["generation_statistics"]["successful_generations"] += 1
                                else:
                                    analysis["generation_statistics"]["failed_generations"] += 1
                                
                                # Track models used
                                variation = gen.get("variation", "unknown")
                                analysis["generation_statistics"]["models_used"][variation] = \
                                    analysis["generation_statistics"]["models_used"].get(variation, 0) + 1
                    else:
                        analysis["posts_without_images"] += 1
                        analysis["missing_image_posts"].append({
                            "post_id": str(post["_id"]),
                            "shortcode": post.get("shortcode", "unknown"),
                            "created_at": post.get("created_at"),
                            "instagram_status": instagram_status
                        })
                else:
                    analysis["posts_without_images"] += 1
                    analysis["missing_image_posts"].append({
                        "post_id": str(post["_id"]),
                        "shortcode": post.get("shortcode", "unknown"),
                        "created_at": post.get("created_at"),
                        "instagram_status": instagram_status
                    })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing posts collection: {e}")
            raise
    
    async def get_posts_needing_images(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get posts that need images generated"""
        try:
            posts_collection = self.db.posts
            post_images_collection = self.db.post_images
            
            # Find posts without proper image references or failed generations
            posts_needing_images = []
            
            # Get posts without image_ref or with failed image generation
            posts = posts_collection.find({
                "$or": [
                    {"image_ref": {"$exists": False}},
                    {"instagram_status": {"$ne": "published"}}
                ]
            }).limit(limit)
            
            for post in posts:
                post_data = {
                    "post_id": str(post["_id"]),
                    "shortcode": post.get("shortcode"),
                    "created_at": post.get("created_at"),
                    "instagram_status": post.get("instagram_status", "unknown"),
                    "has_image_ref": bool(post.get("image_ref")),
                    "image_status": "missing"
                }
                
                # Check if image_ref exists and has valid generations
                if post.get("image_ref"):
                    image_doc = post_images_collection.find_one({"_id": post["image_ref"]})
                    if image_doc and image_doc.get("images"):
                        generations = image_doc["images"][0].get("midjourney_generations", [])
                        successful_gens = [g for g in generations if g.get("midjourney_image_id")]
                        
                        if successful_gens:
                            post_data["image_status"] = "has_images"
                            post_data["generation_count"] = len(successful_gens)
                        else:
                            post_data["image_status"] = "failed_generation"
                            post_data["generation_count"] = 0
                    else:
                        post_data["image_status"] = "no_image_document"
                
                posts_needing_images.append(post_data)
            
            return posts_needing_images
            
        except Exception as e:
            logger.error(f"Error getting posts needing images: {e}")
            raise
    
    async def get_successful_posts_for_analysis(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get successfully published posts for style analysis"""
        try:
            posts_collection = self.db.posts
            post_images_collection = self.db.post_images
            
            # Find published posts with images
            successful_posts = []
            
            posts = posts_collection.find({
                "instagram_status": "published",
                "image_ref": {"$exists": True}
            }).sort("instagram_publish_date", -1).limit(limit)
            
            for post in posts:
                # Get image data
                image_doc = post_images_collection.find_one({"_id": post["image_ref"]})
                
                if image_doc and image_doc.get("images"):
                    generations = image_doc["images"][0].get("midjourney_generations", [])
                    successful_gens = [g for g in generations if g.get("midjourney_image_id")]
                    
                    if successful_gens:
                        post_data = {
                            "post_id": str(post["_id"]),
                            "shortcode": post.get("shortcode"),
                            "instagram_post_id": post.get("instagram_post_id"),
                            "publish_date": post.get("instagram_publish_date"),
                            "generations": []
                        }
                        
                        for gen in successful_gens:
                            post_data["generations"].append({
                                "variation": gen.get("variation"),
                                "prompt": gen.get("prompt"),
                                "image_id": gen.get("midjourney_image_id")
                            })
                        
                        successful_posts.append(post_data)
            
            return successful_posts
            
        except Exception as e:
            logger.error(f"Error getting successful posts: {e}")
            raise
    
    async def extract_prompts_for_style_analysis(self) -> Dict[str, Any]:
        """Extract prompts from successful posts for style analysis"""
        try:
            successful_posts = await self.get_successful_posts_for_analysis(50)
            
            analysis = {
                "total_successful_posts": len(successful_posts),
                "unique_prompts": set(),
                "prompt_patterns": {},
                "variation_usage": {},
                "common_keywords": {},
                "style_trends": []
            }
            
            for post in successful_posts:
                for gen in post["generations"]:
                    prompt = gen.get("prompt", "")
                    variation = gen.get("variation", "unknown")
                    
                    if prompt:
                        analysis["unique_prompts"].add(prompt)
                        
                        # Track variation usage
                        analysis["variation_usage"][variation] = \
                            analysis["variation_usage"].get(variation, 0) + 1
                        
                        # Extract keywords
                        words = prompt.lower().split()
                        for word in words:
                            if len(word) > 3 and not word.startswith("--"):
                                analysis["common_keywords"][word] = \
                                    analysis["common_keywords"].get(word, 0) + 1
            
            # Convert set to list for JSON serialization
            analysis["unique_prompts"] = list(analysis["unique_prompts"])
            
            # Sort keywords by frequency
            analysis["common_keywords"] = dict(
                sorted(analysis["common_keywords"].items(), 
                      key=lambda x: x[1], reverse=True)[:20]
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error extracting prompts for style analysis: {e}")
            raise


# Initialize MongoDB connection
mongodb = SiliconSentimentsMongoDB("mongodb://localhost:27017/")  # Default, will be configurable

# Initialize additional services (will be set up after MongoDB connection)
image_generation = None
instagram_analysis = None

# Create MCP server
server = Server("siliconsentiments-mongodb")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="connect_mongodb",
            description="Connect to MongoDB server on Raspberry Pi",
            inputSchema={
                "type": "object",
                "properties": {
                    "mongodb_uri": {
                        "type": "string",
                        "description": "MongoDB connection URI (e.g., mongodb://192.168.1.100:27017/)"
                    },
                    "db_name": {
                        "type": "string", 
                        "description": "Database name (default: silicon_sentiments)",
                        "default": "silicon_sentiments"
                    }
                },
                "required": ["mongodb_uri"]
            }
        ),
        Tool(
            name="get_database_stats",
            description="Get database statistics and collection information"
        ),
        Tool(
            name="analyze_posts",
            description="Analyze posts collection for missing images and patterns"
        ),
        Tool(
            name="get_posts_needing_images",
            description="Get posts that need images generated",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to return (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_successful_posts",
            description="Get successfully published posts for analysis",
            inputSchema={
                "type": "object", 
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to return (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="analyze_style_patterns",
            description="Analyze prompts and styles from successful posts for brand development"
        ),
        Tool(
            name="close_connection",
            description="Close MongoDB connection"
        ),
        Tool(
            name="generate_missing_images",
            description="Generate images for posts that are missing them using AI providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_generations": {
                        "type": "integer",
                        "description": "Maximum number of images to generate (default: 5)",
                        "default": 5
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration for image generation (providers, etc.)",
                        "properties": {
                            "providers": {
                                "type": "object",
                                "description": "Provider configurations"
                            }
                        }
                    }
                }
            }
        ),
        Tool(
            name="analyze_posting_patterns",
            description="Analyze historical posting patterns for optimization"
        ),
        Tool(
            name="analyze_content_themes",
            description="Analyze content themes from prompts and descriptions"
        ),
        Tool(
            name="identify_success_patterns",
            description="Identify patterns in successful content"
        ),
        Tool(
            name="suggest_improvements",
            description="Get content and posting suggestions based on analysis"
        ),
        Tool(
            name="analyze_generation_performance",
            description="Analyze performance of automated image generations"
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any] | None) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "connect_mongodb":
            if not arguments or "mongodb_uri" not in arguments:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: mongodb_uri is required")],
                    isError=True
                )
            
            mongodb_uri = arguments["mongodb_uri"]
            db_name = arguments.get("db_name", "silicon_sentiments")
            
            # Update MongoDB connection
            global mongodb
            mongodb = SiliconSentimentsMongoDB(mongodb_uri, db_name)
            
            success = await mongodb.connect()
            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"✅ Connected to MongoDB at {mongodb_uri}, database: {db_name}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"❌ Failed to connect to MongoDB at {mongodb_uri}"
                    )],
                    isError=True
                )
        
        elif name == "get_database_stats":
            stats = await mongodb.get_database_stats()
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=f"📊 Database Statistics:\n\n{json.dumps(stats, indent=2, default=str)}"
                )]
            )
        
        elif name == "analyze_posts":
            analysis = await mongodb.analyze_posts_collection()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"📈 Posts Analysis:\n\n{json.dumps(analysis, indent=2, default=str)}"
                )]
            )
        
        elif name == "get_posts_needing_images":
            limit = arguments.get("limit", 10) if arguments else 10
            posts = await mongodb.get_posts_needing_images(limit)
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"🎨 Posts Needing Images ({len(posts)} found):\n\n{json.dumps(posts, indent=2, default=str)}"
                )]
            )
        
        elif name == "get_successful_posts":
            limit = arguments.get("limit", 20) if arguments else 20
            posts = await mongodb.get_successful_posts_for_analysis(limit)
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"✅ Successful Posts ({len(posts)} found):\n\n{json.dumps(posts, indent=2, default=str)}"
                )]
            )
        
        elif name == "analyze_style_patterns":
            analysis = await mongodb.extract_prompts_for_style_analysis()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"🎨 Style Pattern Analysis:\n\n{json.dumps(analysis, indent=2, default=str)}"
                )]
            )
        
        elif name == "close_connection":
            mongodb.close()
            return CallToolResult(
                content=[TextContent(type="text", text="🔌 MongoDB connection closed")]
            )
        
        elif name == "generate_missing_images":
            global image_generation
            
            if not image_generation:
                # Initialize with default config if none provided
                default_config = {
                    "providers": {
                        "replicate": {
                            "api_token": "your_replicate_token_here",
                            "default_model": "flux_schnell"
                        }
                    }
                }
                config = arguments.get("config", default_config) if arguments else default_config
                image_generation = ImageGenerationIntegration(mongodb, config)
                
                if not await image_generation.initialize_generation_service():
                    return CallToolResult(
                        content=[TextContent(type="text", text="❌ Failed to initialize image generation service")],
                        isError=True
                    )
            
            max_generations = arguments.get("max_generations", 5) if arguments else 5
            
            # Get posts needing images
            posts_needing_images = await mongodb.get_posts_needing_images(limit=max_generations)
            
            if not posts_needing_images:
                return CallToolResult(
                    content=[TextContent(type="text", text="✅ No posts need images")]
                )
            
            # Generate images
            results = await image_generation.generate_missing_images(posts_needing_images, max_generations)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"🎨 Image Generation Results:\n\n{json.dumps(results, indent=2, default=str)}"
                )]
            )
        
        elif name == "analyze_posting_patterns":
            global instagram_analysis
            if not instagram_analysis:
                instagram_analysis = InstagramAnalysis(mongodb)
            
            patterns = await instagram_analysis.analyze_posting_patterns()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"📅 Posting Patterns Analysis:\n\n{json.dumps(patterns, indent=2, default=str)}"
                )]
            )
        
        elif name == "analyze_content_themes":
            global instagram_analysis
            if not instagram_analysis:
                instagram_analysis = InstagramAnalysis(mongodb)
            
            themes = await instagram_analysis.analyze_content_themes()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"🎭 Content Themes Analysis:\n\n{json.dumps(themes, indent=2, default=str)}"
                )]
            )
        
        elif name == "identify_success_patterns":
            global instagram_analysis
            if not instagram_analysis:
                instagram_analysis = InstagramAnalysis(mongodb)
            
            patterns = await instagram_analysis.identify_successful_content_patterns()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"🏆 Success Patterns Analysis:\n\n{json.dumps(patterns, indent=2, default=str)}"
                )]
            )
        
        elif name == "suggest_improvements":
            global instagram_analysis
            if not instagram_analysis:
                instagram_analysis = InstagramAnalysis(mongodb)
            
            suggestions = await instagram_analysis.suggest_content_improvements()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"💡 Content Improvement Suggestions:\n\n{json.dumps(suggestions, indent=2, default=str)}"
                )]
            )
        
        elif name == "analyze_generation_performance":
            global image_generation
            if not image_generation:
                return CallToolResult(
                    content=[TextContent(type="text", text="❌ Image generation service not initialized")],
                    isError=True
                )
            
            performance = await image_generation.analyze_successful_prompts()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"📊 Generation Performance Analysis:\n\n{json.dumps(performance, indent=2, default=str)}"
                )]
            )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="siliconsentiments-mongodb",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())