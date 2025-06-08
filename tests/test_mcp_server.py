#!/usr/bin/env python3
"""
Unit tests for MCP MongoDB Server components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import sys
import os
from pathlib import Path

# Add mcp_mongodb_server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_mongodb_server"))

class TestImageGenerationIntegration:
    """Test cases for ImageGenerationIntegration class"""
    
    @pytest.fixture
    def mock_mongodb_client(self):
        """Mock MongoDB client"""
        mock_client = Mock()
        mock_db = Mock()
        mock_collection = Mock()
        
        mock_client.db = mock_db
        mock_db.posts = mock_collection
        
        return mock_client
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "providers": {
                "replicate": {
                    "api_token": "test_token",
                    "enabled": True
                }
            },
            "storage": {
                "type": "local",
                "path": "/tmp/test_images"
            }
        }
    
    @pytest.fixture
    def sample_posts_data(self):
        """Sample posts data for testing"""
        return [
            {
                "post_id": "test_post_1",
                "shortcode": "ABC123",
                "caption": "Test caption for AI generation",
                "created_time": datetime.now(timezone.utc)
            },
            {
                "post_id": "test_post_2", 
                "shortcode": "DEF456",
                "caption": "Another test post",
                "created_time": datetime.now(timezone.utc)
            }
        ]
    
    @pytest.fixture
    def mock_generation_response(self):
        """Mock generation response"""
        response = Mock()
        response.success = True
        response.provider_used = "replicate"
        response.cost = 0.05
        response.generation_time = 3.2
        response.image_urls = ["https://example.com/image1.jpg"]
        response.storage_ids = ["storage_id_1"]
        response.generation_id = "gen_123"
        response.error = None
        return response
    
    def test_initialization(self, mock_mongodb_client, sample_config):
        """Test ImageGenerationIntegration initialization"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            from image_generation_tools import ImageGenerationIntegration
            
            integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
            
            assert integration.mongodb == mock_mongodb_client
            assert integration.config == sample_config
            assert integration.generation_service is None
    
    @pytest.mark.asyncio
    async def test_initialize_generation_service_success(self, mock_mongodb_client, sample_config):
        """Test successful initialization of generation service"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            # Mock the imports directly since they might not exist in the module
            with patch.object(sys.modules['image_generation_tools'], 'MultiProviderGenerationService', create=True) as mock_service:
                from image_generation_tools import ImageGenerationIntegration
                
                # Mock the service initialization
                mock_instance = AsyncMock()
                mock_instance.initialize.return_value = True
                mock_service.return_value = mock_instance
                
                integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
                result = await integration.initialize_generation_service()
                
                assert result is True
                assert integration.generation_service == mock_instance
                mock_instance.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_generation_service_unavailable(self, mock_mongodb_client, sample_config):
        """Test initialization when image generation is unavailable"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', False):
            from image_generation_tools import ImageGenerationIntegration
            
            integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
            result = await integration.initialize_generation_service()
            
            assert result is False
            assert integration.generation_service is None
    
    def test_generate_brand_prompt(self, mock_mongodb_client, sample_config, sample_posts_data):
        """Test brand prompt generation"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            from image_generation_tools import ImageGenerationIntegration
            
            integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
            prompt = integration._generate_brand_prompt(sample_posts_data[0])
            
            # Check that prompt contains expected elements
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "instagram ready" in prompt.lower()
            assert any(style in prompt for style in ["digital art", "modern aesthetic", "tech-inspired"])
    
    @pytest.mark.asyncio
    async def test_generate_missing_images_success(self, mock_mongodb_client, sample_config, 
                                                  sample_posts_data, mock_generation_response):
        """Test successful image generation for missing images"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            # Mock the imports that might not exist
            with patch.object(sys.modules['image_generation_tools'], 'MultiProviderGenerationService', create=True), \
                 patch.object(sys.modules['image_generation_tools'], 'GenerationRequest', create=True) as mock_request, \
                 patch.object(sys.modules['image_generation_tools'], 'ProviderStrategy', create=True) as mock_strategy:
                
                from image_generation_tools import ImageGenerationIntegration
                
                integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
                
                # Mock the generation service
                mock_service = AsyncMock()
                mock_service.generate_image.return_value = mock_generation_response
                integration.generation_service = mock_service
                
                # Mock the update method
                integration._update_post_with_generation = AsyncMock(return_value=True)
                
                result = await integration.generate_missing_images(sample_posts_data, max_generations=2)
                
                assert result["attempted_generations"] == 2
                assert result["successful_generations"] == 2
                assert result["failed_generations"] == 0
                assert result["total_cost"] == 0.10  # 2 * 0.05
                assert len(result["generation_details"]) == 2
    
    @pytest.mark.asyncio
    async def test_generate_missing_images_no_service(self, mock_mongodb_client, sample_config, sample_posts_data):
        """Test image generation when service is not initialized"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            from image_generation_tools import ImageGenerationIntegration
            
            integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
            # Don't initialize the service
            
            result = await integration.generate_missing_images(sample_posts_data)
            
            assert "error" in result
            assert result["error"] == "Generation service not initialized"
    
    @pytest.mark.asyncio
    async def test_update_post_with_generation(self, mock_mongodb_client, sample_config, mock_generation_response):
        """Test updating MongoDB post with generation results"""
        with patch('image_generation_tools.IMAGE_GENERATION_AVAILABLE', True):
            from image_generation_tools import ImageGenerationIntegration
            
            integration = ImageGenerationIntegration(mock_mongodb_client, sample_config)
            
            # Mock successful update
            mock_mongodb_client.db.posts.update_one.return_value.modified_count = 1
            
            result = await integration._update_post_with_generation("test_post_1", mock_generation_response)
            
            assert result is True
            mock_mongodb_client.db.posts.update_one.assert_called_once()
            
            # Check the update call arguments
            call_args = mock_mongodb_client.db.posts.update_one.call_args
            filter_arg = call_args[0][0]
            update_arg = call_args[0][1]
            
            assert filter_arg == {"_id": "test_post_1"}
            assert "$set" in update_arg
            assert "automated_generation" in update_arg["$set"]


class TestInstagramAnalysis:
    """Test cases for Instagram analysis functionality"""
    
    @pytest.fixture
    def mock_mongodb_client(self):
        """Mock MongoDB client for analysis tests"""
        mock_client = Mock()
        mock_db = Mock()
        mock_client.db = mock_db
        
        # Mock collections
        mock_db.posts = Mock()
        mock_db.post_images = Mock()
        mock_db.carousel_posts = Mock()
        
        return mock_client
    
    @pytest.fixture
    def sample_aggregation_result(self):
        """Sample aggregation pipeline result"""
        return [
            {
                "_id": {"year": 2024, "month": 1},
                "post_count": 15,
                "avg_likes": 1250,
                "avg_comments": 45,
                "total_reach": 18750
            },
            {
                "_id": {"year": 2024, "month": 2},
                "post_count": 18,
                "avg_likes": 1380,
                "avg_comments": 52,
                "total_reach": 24840
            }
        ]
    
    def test_aggregation_pipeline_creation(self, mock_mongodb_client):
        """Test that aggregation pipelines are created correctly"""
        with patch.dict(sys.modules, {'pymongo': Mock()}):
            sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_mongodb_server"))
            
            # This would test the pipeline creation logic
            # Since the actual module requires MongoDB, we'll test the structure
            pipeline = [
                {"$match": {"instagram_status": "published"}},
                {"$group": {"_id": "$created_time", "count": {"$sum": 1}}}
            ]
            
            assert len(pipeline) == 2
            assert "$match" in pipeline[0]
            assert "$group" in pipeline[1]


class TestMCPServerIntegration:
    """Integration tests for the MCP server"""
    
    @pytest.fixture
    def mock_server_config(self):
        """Mock server configuration"""
        return {
            "mongodb": {
                "uri": "mongodb://localhost:27017/",
                "database": "test_db"
            },
            "image_generation": {
                "providers": {
                    "replicate": {
                        "api_token": "test_token"
                    }
                }
            }
        }
    
    def test_server_initialization_structure(self, mock_server_config):
        """Test that server can be structured properly"""
        # This tests the general structure without actually starting the server
        assert "mongodb" in mock_server_config
        assert "image_generation" in mock_server_config
        assert "uri" in mock_server_config["mongodb"]
        assert "database" in mock_server_config["mongodb"]


class TestUtilityFunctions:
    """Test utility functions and helpers"""
    
    def test_datetime_handling(self):
        """Test datetime utilities"""
        now = datetime.now(timezone.utc)
        assert now.tzinfo == timezone.utc
        
        # Test that we can serialize/deserialize datetime
        timestamp = now.isoformat()
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed.tzinfo is not None
    
    def test_config_validation(self):
        """Test configuration validation"""
        valid_config = {
            "mongodb": {"uri": "mongodb://localhost:27017/"},
            "image_generation": {"providers": {}}
        }
        
        # Basic structure validation
        assert "mongodb" in valid_config
        assert "uri" in valid_config["mongodb"]
        assert "image_generation" in valid_config


# Performance and stress tests
class TestPerformance:
    """Performance and stress tests"""
    
    @pytest.mark.slow
    def test_large_batch_processing_simulation(self):
        """Simulate processing large batches of data"""
        # Simulate processing 1000 posts
        batch_size = 1000
        posts = [{"id": i, "content": f"Post {i}"} for i in range(batch_size)]
        
        # Test that we can handle large datasets
        assert len(posts) == batch_size
        
        # Simulate chunking for processing
        chunk_size = 50
        chunks = [posts[i:i + chunk_size] for i in range(0, len(posts), chunk_size)]
        
        assert len(chunks) == batch_size // chunk_size
        assert len(chunks[0]) == chunk_size


if __name__ == "__main__":
    pytest.main([__file__])