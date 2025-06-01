"""
Instagram Feed Analysis Framework

This module provides tools to analyze Instagram feed data for content inspiration
and brand development for SiliconSentiments Art.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import re
from collections import Counter

logger = logging.getLogger("instagram_analysis")


class InstagramAnalysis:
    """Instagram content analysis for brand development"""
    
    def __init__(self, mongodb_client):
        """
        Initialize Instagram analysis
        
        Args:
            mongodb_client: MongoDB client instance
        """
        self.mongodb = mongodb_client
    
    async def analyze_posting_patterns(self) -> Dict[str, Any]:
        """
        Analyze posting patterns from historical data
        
        Returns:
            Dict with posting pattern analysis
        """
        try:
            posts_collection = self.mongodb.db.posts
            
            # Get published posts with dates
            posts = list(posts_collection.find({
                "instagram_status": "published",
                "instagram_publish_date": {"$exists": True}
            }).sort("instagram_publish_date", 1))
            
            if not posts:
                return {"error": "No published posts found"}
            
            analysis = {
                "total_posts": len(posts),
                "date_range": {
                    "first_post": None,
                    "last_post": None,
                    "days_active": 0
                },
                "posting_frequency": {
                    "posts_per_day": 0.0,
                    "posts_per_week": 0.0,
                    "posts_per_month": 0.0
                },
                "daily_patterns": {},
                "weekly_patterns": {},
                "monthly_patterns": {},
                "engagement_trends": []
            }
            
            # Extract dates
            publish_dates = []
            for post in posts:
                pub_date = post.get("instagram_publish_date")
                if pub_date:
                    if isinstance(pub_date, str):
                        # Parse string date if needed
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    publish_dates.append(pub_date)
            
            if publish_dates:
                analysis["date_range"]["first_post"] = min(publish_dates)
                analysis["date_range"]["last_post"] = max(publish_dates)
                
                date_diff = max(publish_dates) - min(publish_dates)
                analysis["date_range"]["days_active"] = date_diff.days
                
                if date_diff.days > 0:
                    analysis["posting_frequency"]["posts_per_day"] = len(posts) / date_diff.days
                    analysis["posting_frequency"]["posts_per_week"] = len(posts) / (date_diff.days / 7)
                    analysis["posting_frequency"]["posts_per_month"] = len(posts) / (date_diff.days / 30)
            
            # Analyze patterns by day of week, hour, etc.
            for date in publish_dates:
                # Day of week (0=Monday, 6=Sunday)
                day_name = date.strftime("%A")
                analysis["daily_patterns"][day_name] = \
                    analysis["daily_patterns"].get(day_name, 0) + 1
                
                # Hour of day
                hour = date.hour
                analysis["weekly_patterns"][hour] = \
                    analysis["weekly_patterns"].get(hour, 0) + 1
                
                # Month
                month_name = date.strftime("%B")
                analysis["monthly_patterns"][month_name] = \
                    analysis["monthly_patterns"].get(month_name, 0) + 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing posting patterns: {e}")
            raise
    
    async def analyze_content_themes(self) -> Dict[str, Any]:
        """
        Analyze content themes from prompts and descriptions
        
        Returns:
            Dict with theme analysis
        """
        try:
            posts_collection = self.mongodb.db.posts
            post_images_collection = self.mongodb.db.post_images
            
            # Get posts with images and prompts
            posts = list(posts_collection.find({
                "image_ref": {"$exists": True}
            }))
            
            analysis = {
                "total_posts_analyzed": 0,
                "theme_keywords": {},
                "style_keywords": {},
                "color_themes": {},
                "technical_terms": {},
                "art_styles": {},
                "common_phrases": {},
                "midjourney_parameters": {}
            }
            
            # Keywords that indicate different themes
            theme_categories = {
                "futuristic": ["futuristic", "future", "sci-fi", "technology", "tech", "digital"],
                "abstract": ["abstract", "geometric", "pattern", "fractal", "minimal"],
                "landscape": ["landscape", "cityscape", "environment", "scene", "vista"],
                "portrait": ["portrait", "face", "character", "person", "human"],
                "architectural": ["building", "architecture", "structure", "construction"],
                "artistic": ["painting", "art", "artistic", "creative", "expressive"],
                "nature": ["natural", "organic", "nature", "forest", "ocean", "mountain"]
            }
            
            for post in posts:
                # Get image document
                image_doc = post_images_collection.find_one({"_id": post["image_ref"]})
                
                if image_doc and image_doc.get("images"):
                    generations = image_doc["images"][0].get("midjourney_generations", [])
                    
                    for gen in generations:
                        prompt = gen.get("prompt", "")
                        if prompt:
                            analysis["total_posts_analyzed"] += 1
                            
                            # Analyze prompt content
                            prompt_lower = prompt.lower()
                            words = re.findall(r'\b\w+\b', prompt_lower)
                            
                            # Count theme keywords
                            for theme, keywords in theme_categories.items():
                                for keyword in keywords:
                                    if keyword in prompt_lower:
                                        analysis["theme_keywords"][theme] = \
                                            analysis["theme_keywords"].get(theme, 0) + 1
                            
                            # Extract style terms
                            style_terms = [
                                "realistic", "stylized", "cartoon", "anime", "photorealistic",
                                "minimalist", "detailed", "cinematic", "dramatic", "soft",
                                "vibrant", "muted", "bright", "dark", "colorful"
                            ]
                            
                            for term in style_terms:
                                if term in prompt_lower:
                                    analysis["style_keywords"][term] = \
                                        analysis["style_keywords"].get(term, 0) + 1
                            
                            # Extract Midjourney parameters
                            params = re.findall(r'--\w+\s+[\w\d:.]+', prompt)
                            for param in params:
                                param_name = param.split()[0]
                                analysis["midjourney_parameters"][param_name] = \
                                    analysis["midjourney_parameters"].get(param_name, 0) + 1
                            
                            # Common meaningful words
                            meaningful_words = [w for w in words if len(w) > 3 and w not in [
                                "with", "that", "this", "from", "they", "have", "been", "will"
                            ]]
                            
                            for word in meaningful_words:
                                if not word.startswith("--"):
                                    analysis["common_phrases"][word] = \
                                        analysis["common_phrases"].get(word, 0) + 1
            
            # Sort by frequency
            for category in ["theme_keywords", "style_keywords", "common_phrases", "midjourney_parameters"]:
                analysis[category] = dict(
                    sorted(analysis[category].items(), key=lambda x: x[1], reverse=True)[:15]
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content themes: {e}")
            raise
    
    async def identify_successful_content_patterns(self) -> Dict[str, Any]:
        """
        Identify patterns in successful content for optimization
        
        Returns:
            Dict with success pattern analysis
        """
        try:
            # This would be enhanced with actual engagement data from Instagram
            # For now, we'll analyze based on published vs unpublished posts
            
            posts_collection = self.mongodb.db.posts
            post_images_collection = self.mongodb.db.post_images
            
            # Get published posts (assumed successful)
            successful_posts = list(posts_collection.find({
                "instagram_status": "published",
                "image_ref": {"$exists": True}
            }))
            
            # Get failed posts
            failed_posts = list(posts_collection.find({
                "$or": [
                    {"instagram_status": "failed"},
                    {"image_ref": {"$exists": False}}
                ]
            }))
            
            analysis = {
                "successful_posts": len(successful_posts),
                "failed_posts": len(failed_posts),
                "success_rate": 0.0,
                "successful_patterns": {
                    "common_themes": {},
                    "common_styles": {},
                    "common_parameters": {},
                    "variation_preferences": {}
                },
                "failed_patterns": {
                    "common_themes": {},
                    "common_styles": {},
                    "common_parameters": {}
                },
                "recommendations": []
            }
            
            total_posts = len(successful_posts) + len(failed_posts)
            if total_posts > 0:
                analysis["success_rate"] = len(successful_posts) / total_posts
            
            # Analyze successful patterns
            for post in successful_posts:
                image_doc = post_images_collection.find_one({"_id": post["image_ref"]})
                if image_doc and image_doc.get("images"):
                    generations = image_doc["images"][0].get("midjourney_generations", [])
                    
                    for gen in generations:
                        prompt = gen.get("prompt", "")
                        variation = gen.get("variation", "")
                        
                        # Track variation preferences
                        analysis["successful_patterns"]["variation_preferences"][variation] = \
                            analysis["successful_patterns"]["variation_preferences"].get(variation, 0) + 1
                        
                        # Extract themes and styles from prompt
                        if prompt:
                            self._extract_pattern_keywords(
                                prompt, 
                                analysis["successful_patterns"]
                            )
            
            # Generate recommendations based on patterns
            if analysis["successful_patterns"]["variation_preferences"]:
                most_successful_variation = max(
                    analysis["successful_patterns"]["variation_preferences"].items(),
                    key=lambda x: x[1]
                )[0]
                analysis["recommendations"].append(
                    f"Use {most_successful_variation} variation more often (most successful)"
                )
            
            if analysis["successful_patterns"]["common_themes"]:
                top_themes = list(analysis["successful_patterns"]["common_themes"].items())[:3]
                analysis["recommendations"].append(
                    f"Focus on themes: {', '.join([theme for theme, _ in top_themes])}"
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error identifying successful patterns: {e}")
            raise
    
    def _extract_pattern_keywords(self, prompt: str, patterns: Dict[str, Any]):
        """
        Extract keywords from prompt for pattern analysis
        
        Args:
            prompt: Prompt text
            patterns: Patterns dictionary to update
        """
        prompt_lower = prompt.lower()
        
        # Theme keywords
        theme_keywords = [
            "digital", "abstract", "futuristic", "tech", "silicon", "circuit",
            "geometric", "minimal", "landscape", "cityscape", "portrait"
        ]
        
        for keyword in theme_keywords:
            if keyword in prompt_lower:
                patterns["common_themes"][keyword] = \
                    patterns["common_themes"].get(keyword, 0) + 1
        
        # Style keywords
        style_keywords = [
            "vibrant", "dark", "bright", "colorful", "minimalist", "detailed",
            "realistic", "artistic", "clean", "modern"
        ]
        
        for keyword in style_keywords:
            if keyword in prompt_lower:
                patterns["common_styles"][keyword] = \
                    patterns["common_styles"].get(keyword, 0) + 1
        
        # Extract parameters
        params = re.findall(r'--\w+', prompt)
        for param in params:
            patterns["common_parameters"][param] = \
                patterns["common_parameters"].get(param, 0) + 1
    
    async def suggest_content_improvements(self) -> Dict[str, Any]:
        """
        Suggest content improvements based on analysis
        
        Returns:
            Dict with improvement suggestions
        """
        try:
            # Analyze current patterns
            themes_analysis = await self.analyze_content_themes()
            success_patterns = await self.identify_successful_content_patterns()
            posting_patterns = await self.analyze_posting_patterns()
            
            suggestions = {
                "content_suggestions": [],
                "posting_schedule_suggestions": [],
                "style_suggestions": [],
                "technical_suggestions": [],
                "brand_development": []
            }
            
            # Content suggestions
            if themes_analysis.get("theme_keywords"):
                top_themes = list(themes_analysis["theme_keywords"].items())[:3]
                suggestions["content_suggestions"].append(
                    f"Continue focusing on successful themes: {', '.join([t[0] for t in top_themes])}"
                )
            
            # Posting schedule suggestions
            if posting_patterns.get("posting_frequency", {}).get("posts_per_day", 0) < 1:
                suggestions["posting_schedule_suggestions"].append(
                    "Consider increasing posting frequency to at least 1 post per day for better engagement"
                )
            
            # Style suggestions based on successful patterns
            if success_patterns.get("successful_patterns", {}).get("common_styles"):
                top_styles = list(success_patterns["successful_patterns"]["common_styles"].items())[:3]
                suggestions["style_suggestions"].append(
                    f"Use successful style elements: {', '.join([s[0] for s in top_styles])}"
                )
            
            # Brand development suggestions
            suggestions["brand_development"].extend([
                "Develop consistent color palette based on most successful posts",
                "Create template prompts for different content categories",
                "Experiment with trending art styles while maintaining brand identity",
                "Consider seasonal content themes for better relevance"
            ])
            
            # Technical suggestions
            if themes_analysis.get("midjourney_parameters"):
                suggestions["technical_suggestions"].append(
                    "Optimize Midjourney parameters based on successful generations"
                )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating content suggestions: {e}")
            raise