#!/usr/bin/env python3
"""
pytest configuration for carousel extraction tests
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "browser: marks tests that require real browser"
    )

def pytest_collection_modifyitems(config, items):
    """Add markers to tests automatically"""
    for item in items:
        # Mark browser tests
        if "browser" in item.name or "test_carousel" in str(item.fspath):
            item.add_marker(pytest.mark.browser)
        
        # Mark slow tests
        if any(keyword in item.name for keyword in ["performance", "all_images", "download"]):
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "extract" in item.name or "navigate" in item.name:
            item.add_marker(pytest.mark.integration)

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return {
        "shortcode": "C0xFHGOrBN7",
        "output_dir": "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7",
        "timeout": 30,
        "max_images": 10,
        "min_images": 2
    }