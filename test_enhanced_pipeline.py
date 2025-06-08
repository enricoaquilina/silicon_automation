#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Multi-Model Pipeline
- Unit tests for individual components
- Integration tests for VLM and generation workflows  
- End-to-end tests for complete pipeline
- Mock and real API testing
"""

import unittest
import asyncio
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from PIL import Image
import base64
from datetime import datetime
from typing import Dict, Any, List

# Import our pipeline
from enhanced_multi_model_pipeline import EnhancedMultiModelPipeline


class TestEnhancedMultiModelPipeline(unittest.TestCase):
    """Unit tests for individual pipeline components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_token = "test_token_123"
        self.test_mongodb_uri = "mongodb://test:27017/"
        self.pipeline = EnhancedMultiModelPipeline(self.test_token, self.test_mongodb_uri)
        
        # Create test image
        self.test_image_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_image_dir, "test_image.jpg")
        
        # Create a simple test image
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img.save(self.test_image_path, 'JPEG')
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_image_dir):
            shutil.rmtree(self.test_image_dir)
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        self.assertEqual(self.pipeline.replicate_token, self.test_token)
        self.assertEqual(self.pipeline.mongodb_uri, self.test_mongodb_uri)
        self.assertEqual(self.pipeline.replicate_api_url, "https://api.replicate.com/v1/predictions")
        
    def test_available_models_configuration(self):
        """Test that all models are properly configured"""
        models = self.pipeline.AVAILABLE_MODELS
        
        # Check required models exist
        self.assertIn("flux-1.1-pro", models)
        self.assertIn("recraft-v3", models)
        self.assertIn("sdxl", models) 
        self.assertIn("minimax-video", models)
        self.assertIn("playground-v2_5", models)
        self.assertIn("kandinsky-2.2", models)
        
        # Check each model has required fields
        for model_name, config in models.items():
            self.assertIn("version", config)
            self.assertIn("cost_per_image", config)
            self.assertIn("short_name", config)
            self.assertIn("description", config)
            
            # Check types
            self.assertIsInstance(config["version"], str)
            self.assertIsInstance(config["cost_per_image"], (int, float))
            self.assertIsInstance(config["short_name"], str)
            self.assertIsInstance(config["description"], str)
    
    def test_enhanced_prompt_generation(self):
        """Test SiliconSentiments prompt generation"""
        description = "a digital painting of a woman's face"
        shortcode = "C0xFHGOrBN7"
        
        prompt = self.pipeline.create_enhanced_siliconsentiments_prompt(description, shortcode)
        
        # Check prompt contains key elements
        self.assertIn("SiliconSentiments", prompt)
        self.assertIn("cyborg-nature fusion", prompt)
        self.assertIn("BIOMECHANICAL ELEMENTS", prompt)
        self.assertIn("NATURE FUSION", prompt)
        self.assertIn("SCI-FI TECHNOLOGY", prompt)
        self.assertIn("VISUAL STYLE", prompt)
        self.assertIn("COLOR PALETTE", prompt)
        self.assertIn(description, prompt)
        
        # Check prompt is reasonable length
        self.assertGreater(len(prompt), 500)
        self.assertLess(len(prompt), 2000)
    
    def test_metadata_structure(self):
        """Test metadata creation and structure"""
        test_metadata = {
            "siliconsentiments_generation": {
                "model_name": "flux-1.1-pro",
                "source_shortcode": "TEST123",
                "brand": "SiliconSentiments"
            },
            "technical_info": {
                "format": "JPEG",
                "file_size_bytes": 12345
            }
        }
        
        # Test metadata embedding
        result_path = self.pipeline.add_metadata_to_image(self.test_image_path, test_metadata)
        self.assertEqual(result_path, self.test_image_path)
        self.assertTrue(os.path.exists(result_path))


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for VLM and generation workflows"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_token = os.getenv("REPLICATE_API_TOKEN_TEST", "test_token")
        self.pipeline = EnhancedMultiModelPipeline(self.test_token)
        
        # Create test image
        self.test_image_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_image_dir, "test_image.jpg")
        
        test_img = Image.new('RGB', (512, 512), color='blue')
        test_img.save(self.test_image_path, 'JPEG')
        
    def tearDown(self):
        """Clean up integration test environment"""
        if os.path.exists(self.test_image_dir):
            shutil.rmtree(self.test_image_dir)
    
    @patch('aiohttp.ClientSession')
    async def test_blip_vlm_analysis_mock(self, mock_session):
        """Test BLIP VLM analysis with mocked API"""
        # Mock successful BLIP response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"id": "test_prediction_123"}
        
        mock_get_response = AsyncMock()
        mock_get_response.json.return_value = {
            "status": "succeeded",
            "output": "a beautiful digital artwork"
        }
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session_instance.get.return_value.__aenter__.return_value = mock_get_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        result = await self.pipeline.analyze_image_with_blip(self.test_image_path)
        
        self.assertIn("a beautiful digital artwork", result)
    
    @patch('aiohttp.ClientSession')
    async def test_flux_generation_mock(self, mock_session):
        """Test Flux generation with mocked API"""
        test_prompt = "SiliconSentiments cyborg artwork"
        
        # Mock successful generation response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"id": "test_generation_456"}
        
        mock_get_response = AsyncMock()
        mock_get_response.json.return_value = {
            "status": "succeeded", 
            "output": ["https://example.com/generated1.jpg", "https://example.com/generated2.jpg"]
        }
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session_instance.get.return_value.__aenter__.return_value = mock_get_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        result = await self.pipeline.generate_with_model(test_prompt, "flux-schnell", num_outputs=2)
        
        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/generated1.jpg", result)
    
    @patch('pymongo.MongoClient')
    def test_mongodb_connection_mock(self, mock_client):
        """Test MongoDB connection with mocking"""
        mock_client_instance = Mock()
        mock_client_instance.admin.command.return_value = {"ok": 1}
        mock_client.return_value = mock_client_instance
        
        result = self.pipeline.connect_to_mongodb()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.pipeline.client)


class TestEndToEndPipeline(unittest.TestCase):
    """End-to-end tests for complete pipeline"""
    
    def setUp(self):
        """Set up E2E test environment"""
        self.test_token = os.getenv("REPLICATE_API_TOKEN_TEST", "test_token")
        self.pipeline = EnhancedMultiModelPipeline(self.test_token)
        
        # Create test image
        self.test_image_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_image_dir, "test_image.jpg")
        
        test_img = Image.new('RGB', (1024, 1024), color='green')
        test_img.save(self.test_image_path, 'JPEG')
        
    def tearDown(self):
        """Clean up E2E test environment"""
        if os.path.exists(self.test_image_dir):
            shutil.rmtree(self.test_image_dir)
    
    @patch('enhanced_multi_model_pipeline.EnhancedMultiModelPipeline.connect_to_mongodb')
    @patch('enhanced_multi_model_pipeline.EnhancedMultiModelPipeline.analyze_image_with_blip')
    @patch('enhanced_multi_model_pipeline.EnhancedMultiModelPipeline.generate_with_model')
    @patch('enhanced_multi_model_pipeline.EnhancedMultiModelPipeline.download_and_save_images')
    async def test_complete_pipeline_mock(self, mock_download, mock_generate, mock_blip, mock_mongodb):
        """Test complete pipeline with all components mocked"""
        
        # Setup mocks
        mock_mongodb.return_value = True
        mock_blip.return_value = "a sci-fi digital artwork"
        mock_generate.return_value = ["https://example.com/gen1.jpg", "https://example.com/gen2.jpg"]
        mock_download.return_value = [
            {
                "filename": "TEST123_flux_v1.jpg",
                "filepath": "/tmp/test1.jpg",
                "size_bytes": 123456,
                "variation": 1,
                "model_name": "flux-1.1-pro",
                "gridfs_id": "test_gridfs_id_1"
            },
            {
                "filename": "TEST123_flux_v2.jpg", 
                "filepath": "/tmp/test2.jpg",
                "size_bytes": 123456,
                "variation": 2,
                "model_name": "flux-1.1-pro",
                "gridfs_id": "test_gridfs_id_2"
            }
        ]
        
        # Run pipeline
        result = await self.pipeline.process_image_with_models(
            self.test_image_path, 
            "TEST123", 
            self.test_image_dir,
            models=["flux-1.1-pro"]
        )
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["shortcode"], "TEST123")
        self.assertEqual(result["successful_models"], ["flux-1.1-pro"])
        self.assertEqual(result["total_variations_generated"], 2)
        self.assertGreater(result["total_cost"], 0)
        
        # Verify mocks were called
        mock_mongodb.assert_called_once()
        mock_blip.assert_called_once_with(self.test_image_path)
        mock_generate.assert_called_once()
        mock_download.assert_called_once()


class TestRealAPIIntegration(unittest.TestCase):
    """Real API integration tests (requires valid API token)"""
    
    def setUp(self):
        """Set up real API test environment"""
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            self.skipTest("REPLICATE_API_TOKEN not set - skipping real API tests")
        
        self.pipeline = EnhancedMultiModelPipeline(self.api_token)
        
        # Create test image
        self.test_image_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_image_dir, "real_test_image.jpg")
        
        # Create a more realistic test image
        test_img = Image.new('RGB', (512, 512), color=(100, 150, 200))
        test_img.save(self.test_image_path, 'JPEG')
        
    def tearDown(self):
        """Clean up real API test environment"""
        if os.path.exists(self.test_image_dir):
            shutil.rmtree(self.test_image_dir)
    
    async def test_real_blip_analysis(self):
        """Test real BLIP VLM analysis (costs ~$0.00)"""
        if not self.api_token:
            self.skipTest("No API token for real testing")
            
        result = await self.pipeline.analyze_image_with_blip(self.test_image_path)
        
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)
        self.assertIn("Caption:", result)
    
    async def test_real_flux_generation(self):
        """Test real Flux generation (costs ~$0.003)"""
        if not self.api_token:
            self.skipTest("No API token for real testing")
            
        test_prompt = "SiliconSentiments cyborg nature fusion: simple test artwork"
        
        result = await self.pipeline.generate_with_model(test_prompt, "flux-1.1-pro", num_outputs=1)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("https://"))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up error testing environment"""
        self.pipeline = EnhancedMultiModelPipeline("invalid_token")
        
    def test_invalid_model_name(self):
        """Test handling of invalid model names"""
        with self.assertRaises(Exception) as context:
            asyncio.run(self.pipeline.generate_with_model("test prompt", "invalid_model"))
        
        self.assertIn("not available", str(context.exception))
    
    def test_missing_image_file(self):
        """Test handling of missing image files"""
        with self.assertRaises(Exception):
            asyncio.run(self.pipeline.analyze_image_with_blip("/nonexistent/path.jpg"))
    
    def test_invalid_mongodb_uri(self):
        """Test handling of invalid MongoDB connection"""
        pipeline = EnhancedMultiModelPipeline("test_token", "invalid://uri")
        result = pipeline.connect_to_mongodb()
        self.assertFalse(result)


class TestPerformanceAndScaling(unittest.TestCase):
    """Test performance characteristics and scaling"""
    
    def setUp(self):
        """Set up performance test environment""" 
        self.pipeline = EnhancedMultiModelPipeline("test_token")
    
    def test_prompt_generation_speed(self):
        """Test prompt generation performance"""
        description = "a complex digital artwork with many elements"
        shortcode = "TEST123"
        
        start_time = datetime.now()
        
        # Generate multiple prompts
        for i in range(100):
            prompt = self.pipeline.create_enhanced_siliconsentiments_prompt(
                f"{description} variation {i}", f"{shortcode}_{i}"
            )
            self.assertGreater(len(prompt), 100)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Should be very fast - under 1 second for 100 prompts
        self.assertLess(duration, 1.0)
    
    def test_metadata_embedding_performance(self):
        """Test metadata embedding performance"""
        # Create test image
        test_dir = tempfile.mkdtemp()
        test_path = os.path.join(test_dir, "perf_test.jpg")
        
        test_img = Image.new('RGB', (1024, 1024), color='red')
        test_img.save(test_path, 'JPEG')
        
        try:
            test_metadata = {
                "test_data": {"key": "value" * 100},  # Larger metadata
                "performance_test": True
            }
            
            start_time = datetime.now()
            result = self.pipeline.add_metadata_to_image(test_path, test_metadata)
            duration = (datetime.now() - start_time).total_seconds()
            
            self.assertEqual(result, test_path)
            self.assertLess(duration, 0.5)  # Should be under 0.5 seconds
            
        finally:
            shutil.rmtree(test_dir)


def run_unit_tests():
    """Run unit tests only"""
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEnhancedMultiModelPipeline))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceAndScaling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_integration_tests():
    """Run integration tests"""
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPipelineIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_e2e_tests():
    """Run end-to-end tests"""
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEndToEndPipeline))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_real_api_tests():
    """Run real API tests (requires token and costs money)"""
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealAPIIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_all_tests():
    """Run all tests"""
    print("🚀 RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Unit tests
    print("\n1️⃣ UNIT TESTS")
    print("-" * 30)
    unit_result = run_unit_tests()
    
    # Integration tests
    print("\n2️⃣ INTEGRATION TESTS") 
    print("-" * 30)
    integration_result = run_integration_tests()
    
    # E2E tests
    print("\n3️⃣ END-TO-END TESTS")
    print("-" * 30)
    e2e_result = run_e2e_tests()
    
    # Real API tests (optional)
    if os.getenv("REPLICATE_API_TOKEN"):
        print("\n4️⃣ REAL API TESTS")
        print("-" * 30)
        api_result = run_real_api_tests()
    else:
        print("\n4️⃣ REAL API TESTS - SKIPPED (no API token)")
        api_result = None
    
    # Summary
    print("\n🎉 TEST SUMMARY")
    print("=" * 60)
    print(f"Unit Tests: {'✅ PASSED' if unit_result.wasSuccessful() else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_result.wasSuccessful() else '❌ FAILED'}")
    print(f"E2E Tests: {'✅ PASSED' if e2e_result.wasSuccessful() else '❌ FAILED'}")
    if api_result:
        print(f"Real API Tests: {'✅ PASSED' if api_result.wasSuccessful() else '❌ FAILED'}")
    
    all_passed = (unit_result.wasSuccessful() and 
                  integration_result.wasSuccessful() and 
                  e2e_result.wasSuccessful() and
                  (api_result is None or api_result.wasSuccessful()))
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Pipeline ready for production.")
    else:
        print("\n❌ SOME TESTS FAILED. Please review and fix issues.")
    
    return all_passed


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "unit":
            run_unit_tests()
        elif test_type == "integration":
            asyncio.run(run_integration_tests())
        elif test_type == "e2e":
            asyncio.run(run_e2e_tests())
        elif test_type == "api":
            asyncio.run(run_real_api_tests())
        elif test_type == "all":
            run_all_tests()
        else:
            print("Usage: python test_enhanced_pipeline.py [unit|integration|e2e|api|all]")
    else:
        run_all_tests()