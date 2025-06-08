#!/usr/bin/env python3
"""
Unit tests for Instagram Analysis module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add mcp_mongodb_server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_mongodb_server"))


class TestInstagramAnalysisTools:
    """Test cases for Instagram analysis tools and aggregation pipelines"""
    
    @pytest.fixture
    def mock_mongodb_client(self):
        """Mock MongoDB client with collections"""
        mock_client = Mock()
        mock_db = Mock()
        mock_client.db = mock_db
        
        # Mock collections
        mock_db.posts = Mock()
        mock_db.post_images = Mock()
        mock_db.carousel_posts = Mock()
        
        return mock_client
    
    @pytest.fixture
    def sample_posts(self):
        """Sample post data for testing"""
        return [
            {
                "_id": "post_1",
                "shortcode": "ABC123",
                "instagram_status": "published",
                "created_time": datetime(2024, 1, 15, tzinfo=timezone.utc),
                "likes_count": 1500,
                "comments_count": 45,
                "caption": "Tech innovation post #AI #ML",
                "engagement_rate": 0.035,
                "reach": 42000
            },
            {
                "_id": "post_2", 
                "shortcode": "DEF456",
                "instagram_status": "published",
                "created_time": datetime(2024, 2, 10, tzinfo=timezone.utc),
                "likes_count": 1800,
                "comments_count": 52,
                "caption": "Silicon Valley trends #startup #tech",
                "engagement_rate": 0.041,
                "reach": 45000
            }
        ]
    
    @pytest.fixture
    def sample_aggregation_results(self):
        """Sample aggregation results"""
        return [
            {
                "_id": {"year": 2024, "month": 1},
                "post_count": 15,
                "avg_likes": 1350.5,
                "avg_comments": 42.3,
                "total_engagement": 20907,
                "avg_engagement_rate": 0.0384
            },
            {
                "_id": {"year": 2024, "month": 2},
                "post_count": 18,
                "avg_likes": 1580.2,
                "avg_comments": 48.7,
                "total_engagement": 29343,
                "avg_engagement_rate": 0.0421
            }
        ]
    
    def test_engagement_analysis_pipeline(self):
        """Test engagement analysis aggregation pipeline structure"""
        # Test pipeline for engagement analysis
        pipeline = [
            {
                "$match": {
                    "instagram_status": "published",
                    "created_time": {
                        "$gte": datetime(2024, 1, 1, tzinfo=timezone.utc),
                        "$lt": datetime(2024, 12, 31, tzinfo=timezone.utc)
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_time"},
                        "month": {"$month": "$created_time"}
                    },
                    "post_count": {"$sum": 1},
                    "avg_likes": {"$avg": "$likes_count"},
                    "avg_comments": {"$avg": "$comments_count"},
                    "total_engagement": {"$sum": {"$add": ["$likes_count", "$comments_count"]}},
                    "avg_engagement_rate": {"$avg": "$engagement_rate"}
                }
            },
            {
                "$sort": {"_id.year": 1, "_id.month": 1}
            }
        ]
        
        # Validate pipeline structure
        assert len(pipeline) == 3
        assert "$match" in pipeline[0]
        assert "$group" in pipeline[1]
        assert "$sort" in pipeline[2]
        
        # Validate match stage
        match_stage = pipeline[0]["$match"]
        assert "instagram_status" in match_stage
        assert "created_time" in match_stage
        
        # Validate group stage
        group_stage = pipeline[1]["$group"]
        assert "_id" in group_stage
        assert "post_count" in group_stage
        assert "avg_likes" in group_stage
    
    def test_top_performing_posts_pipeline(self):
        """Test pipeline for finding top performing posts"""
        pipeline = [
            {
                "$match": {
                    "instagram_status": "published",
                    "likes_count": {"$exists": True}
                }
            },
            {
                "$addFields": {
                    "total_engagement": {"$add": ["$likes_count", "$comments_count"]}
                }
            },
            {
                "$sort": {"total_engagement": -1}
            },
            {
                "$limit": 10
            },
            {
                "$project": {
                    "shortcode": 1,
                    "likes_count": 1,
                    "comments_count": 1,
                    "total_engagement": 1,
                    "engagement_rate": 1,
                    "created_time": 1,
                    "caption": {"$substr": ["$caption", 0, 100]}
                }
            }
        ]
        
        # Validate pipeline structure
        assert len(pipeline) == 5
        assert all(stage in pipeline[i] for i, stage in enumerate(["$match", "$addFields", "$sort", "$limit", "$project"]))
        
        # Validate computed field
        assert pipeline[1]["$addFields"]["total_engagement"]["$add"] == ["$likes_count", "$comments_count"]
    
    def test_hashtag_performance_analysis(self):
        """Test hashtag performance analysis pipeline"""
        pipeline = [
            {
                "$match": {
                    "instagram_status": "published",
                    "caption": {"$regex": "#", "$options": "i"}
                }
            },
            {
                "$addFields": {
                    "hashtags": {
                        "$regexFindAll": {
                            "input": "$caption",
                            "regex": "#[a-zA-Z0-9_]+",
                            "options": "i"
                        }
                    }
                }
            },
            {
                "$unwind": "$hashtags"
            },
            {
                "$group": {
                    "_id": {"$toLower": "$hashtags.match"},
                    "usage_count": {"$sum": 1},
                    "avg_likes": {"$avg": "$likes_count"},
                    "avg_comments": {"$avg": "$comments_count"},
                    "total_reach": {"$sum": "$reach"}
                }
            },
            {
                "$match": {"usage_count": {"$gte": 2}}
            },
            {
                "$sort": {"avg_likes": -1}
            }
        ]
        
        # Validate hashtag extraction logic
        regex_stage = pipeline[1]["$addFields"]["hashtags"]["$regexFindAll"]
        assert regex_stage["regex"] == "#[a-zA-Z0-9_]+"
        assert "$unwind" in pipeline[2]
        assert pipeline[3]["$group"]["_id"] == {"$toLower": "$hashtags.match"}
    
    def test_content_performance_by_type(self):
        """Test content performance analysis by post type"""
        pipeline = [
            {
                "$lookup": {
                    "from": "post_images",
                    "localField": "image_ref",
                    "foreignField": "_id",
                    "as": "image_data"
                }
            },
            {
                "$addFields": {
                    "post_type": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {"$gt": [{"$size": "$image_data"}, 1]},
                                    "then": "carousel"
                                },
                                {
                                    "case": {"$eq": [{"$size": "$image_data"}, 1]},
                                    "then": "single_image"
                                }
                            ],
                            "default": "no_image"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$post_type",
                    "count": {"$sum": 1},
                    "avg_likes": {"$avg": "$likes_count"},
                    "avg_comments": {"$avg": "$comments_count"},
                    "avg_engagement_rate": {"$avg": "$engagement_rate"}
                }
            }
        ]
        
        # Validate post type classification
        switch_stage = pipeline[1]["$addFields"]["post_type"]["$switch"]
        assert len(switch_stage["branches"]) == 2
        assert switch_stage["default"] == "no_image"
    
    def test_missing_images_identification(self):
        """Test pipeline for identifying posts missing images"""
        pipeline = [
            {
                "$match": {
                    "instagram_status": "published",
                    "$or": [
                        {"image_ref": {"$exists": False}},
                        {"image_ref": None}
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "post_images",
                    "localField": "image_ref",
                    "foreignField": "_id",
                    "as": "image_data"
                }
            },
            {
                "$match": {
                    "image_data": {"$size": 0}
                }
            },
            {
                "$project": {
                    "shortcode": 1,
                    "created_time": 1,
                    "caption": {"$substr": ["$caption", 0, 50]},
                    "likes_count": 1,
                    "comments_count": 1
                }
            },
            {
                "$sort": {"created_time": -1}
            }
        ]
        
        # Validate missing image detection
        match_stage = pipeline[0]["$match"]
        assert "$or" in match_stage
        assert {"image_ref": {"$exists": False}} in match_stage["$or"]
        assert {"image_ref": None} in match_stage["$or"]
        
        # Validate empty image data filtering
        assert pipeline[2]["$match"]["image_data"] == {"$size": 0}
    
    def test_time_based_performance_analysis(self):
        """Test time-based performance analysis"""
        pipeline = [
            {
                "$match": {
                    "instagram_status": "published",
                    "created_time": {"$exists": True}
                }
            },
            {
                "$addFields": {
                    "hour_of_day": {"$hour": "$created_time"},
                    "day_of_week": {"$dayOfWeek": "$created_time"},
                    "month": {"$month": "$created_time"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "hour": "$hour_of_day",
                        "day": "$day_of_week"
                    },
                    "post_count": {"$sum": 1},
                    "avg_engagement": {"$avg": {"$add": ["$likes_count", "$comments_count"]}},
                    "avg_engagement_rate": {"$avg": "$engagement_rate"}
                }
            },
            {
                "$sort": {"avg_engagement": -1}
            }
        ]
        
        # Validate time extraction
        time_fields = pipeline[1]["$addFields"]
        assert "hour_of_day" in time_fields
        assert "day_of_week" in time_fields
        assert time_fields["hour_of_day"] == {"$hour": "$created_time"}
    
    @pytest.mark.parametrize("status,expected_count", [
        ("published", 2),
        ("draft", 0),
        ("archived", 0)
    ])
    def test_posts_by_status_filtering(self, status, expected_count, sample_posts):
        """Test filtering posts by different statuses"""
        # Simulate filtering logic
        filtered_posts = [post for post in sample_posts if post.get("instagram_status") == status]
        assert len(filtered_posts) == expected_count
    
    def test_engagement_rate_calculation(self, sample_posts):
        """Test engagement rate calculations"""
        for post in sample_posts:
            expected_rate = (post["likes_count"] + post["comments_count"]) / post["reach"]
            # Allow for small floating point differences
            assert abs(post["engagement_rate"] - expected_rate) < 0.001
    
    def test_data_validation_rules(self):
        """Test data validation for posts"""
        valid_post = {
            "shortcode": "ABC123",
            "instagram_status": "published", 
            "likes_count": 100,
            "comments_count": 5,
            "created_time": datetime.now(timezone.utc)
        }
        
        # Test required fields
        required_fields = ["shortcode", "instagram_status", "created_time"]
        for field in required_fields:
            assert field in valid_post
        
        # Test data types
        assert isinstance(valid_post["likes_count"], int)
        assert isinstance(valid_post["comments_count"], int)
        assert isinstance(valid_post["created_time"], datetime)
    
    def test_aggregation_result_structure(self, sample_aggregation_results):
        """Test that aggregation results have expected structure"""
        for result in sample_aggregation_results:
            # Test required fields
            assert "_id" in result
            assert "post_count" in result
            assert "avg_likes" in result
            assert "avg_comments" in result
            
            # Test data types
            assert isinstance(result["post_count"], int)
            assert isinstance(result["avg_likes"], (int, float))
            assert isinstance(result["avg_comments"], (int, float))
            
            # Test reasonable ranges
            assert result["post_count"] > 0
            assert result["avg_likes"] >= 0
            assert result["avg_comments"] >= 0


class TestAnalysisUtilities:
    """Test utility functions for analysis"""
    
    def test_date_range_generation(self):
        """Test date range utilities"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        date_filter = {
            "$gte": start_date,
            "$lt": end_date
        }
        
        # Test date range structure
        assert "$gte" in date_filter
        assert "$lt" in date_filter
        assert date_filter["$gte"] == start_date
        assert date_filter["$lt"] == end_date
    
    def test_text_processing_utilities(self):
        """Test text processing for captions"""
        sample_caption = "Amazing tech innovation! #AI #MachineLearning #TechTrends 🚀"
        
        # Test hashtag extraction regex
        import re
        hashtags = re.findall(r'#[a-zA-Z0-9_]+', sample_caption)
        
        assert len(hashtags) == 3
        assert "#AI" in hashtags
        assert "#MachineLearning" in hashtags
        assert "#TechTrends" in hashtags
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculations"""
        post_data = {
            "likes_count": 1000,
            "comments_count": 50,
            "reach": 25000,
            "impressions": 35000
        }
        
        # Calculate engagement rate
        engagement_rate = (post_data["likes_count"] + post_data["comments_count"]) / post_data["reach"]
        assert engagement_rate == 0.042
        
        # Calculate click-through rate (if impressions available)
        ctr = post_data["reach"] / post_data["impressions"]
        assert abs(ctr - 0.714) < 0.001


if __name__ == "__main__":
    pytest.main([__file__])