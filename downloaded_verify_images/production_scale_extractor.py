#!/usr/bin/env python3
"""
Production Instagram Carousel Extractor for 2000+ Posts
- Rate limiting: 2-5 second delays between requests
- Batch processing: 50 posts per batch with 5-minute cooldowns
- Robust error handling with retries
- Progress tracking and resumption
- MongoDB integration for deduplication
"""

import time
import random
from datetime import datetime, timedelta

class ProductionCarouselExtractor:
    def __init__(self):
        self.rate_limits = {
            "request_delay": (2, 5),    # 2-5 seconds between posts
            "batch_size": 50,           # Posts per batch 
            "batch_cooldown": 300,      # 5 minutes between batches
            "daily_limit": 1000,        # Max posts per day
            "hourly_limit": 100         # Max posts per hour
        }
        
        self.session_stats = {
            "processed": 0,
            "successful": 0, 
            "failed": 0,
            "start_time": datetime.now(),
            "last_batch": None
        }
    
    def process_batch(self, posts_batch):
        """Process a batch of posts with rate limiting"""
        for post in posts_batch:
            # Rate limiting
            delay = random.uniform(*self.rate_limits["request_delay"])
            time.sleep(delay)
            
            # Extract carousel (using methods above)
            success = self.extract_single_carousel(post["shortcode"])
            
            if success:
                self.session_stats["successful"] += 1
            else:
                self.session_stats["failed"] += 1
            
            self.session_stats["processed"] += 1
    
    def run_production_extraction(self, total_posts=2000):
        """Run production extraction with proper scaling"""
        batch_size = self.rate_limits["batch_size"]
        
        for batch_start in range(0, total_posts, batch_size):
            batch_end = min(batch_start + batch_size, total_posts)
            print(f"Processing batch {batch_start}-{batch_end}/{total_posts}")
            
            # Get posts batch from database
            posts_batch = self.get_posts_batch(batch_start, batch_end)
            
            # Process batch
            self.process_batch(posts_batch)
            
            # Batch cooldown (except for last batch)
            if batch_end < total_posts:
                print(f"Batch cooldown: {self.rate_limits['batch_cooldown']}s")
                time.sleep(self.rate_limits["batch_cooldown"])

# Usage for 2000+ posts:
# extractor = ProductionCarouselExtractor()
# extractor.run_production_extraction(2000)
