#!/usr/bin/env python3
"""
Simple BrowserMCP Test - Test basic functionality
"""

import asyncio
import time

def test_browsermcp_navigation():
    """Test basic BrowserMCP navigation"""
    print("🧪 Testing BrowserMCP navigation...")
    
    try:
        # Test navigation to Instagram
        url = "https://www.instagram.com/p/C0xFHGOrBN7/"
        print(f"   🔍 Navigating to {url}")
        
        result = mcp__browsermcp__browser_navigate(url=url)
        print(f"   ✅ Navigation result: {result}")
        
        # Wait for page load
        time.sleep(3)
        
        # Test taking a snapshot
        print("   📸 Taking snapshot...")
        snapshot = mcp__browsermcp__browser_snapshot()
        print(f"   📊 Snapshot result: {type(snapshot)}")
        
        # Test clicking (will likely fail but let's see the error)
        print("   🖱️  Testing click...")
        try:
            click_result = mcp__browsermcp__browser_click(
                element="any button",
                ref="button"
            )
            print(f"   ✅ Click result: {click_result}")
        except Exception as e:
            print(f"   ⚠️  Click failed (expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 SIMPLE BROWSERMCP TEST")
    print("=" * 40)
    
    success = test_browsermcp_navigation()
    
    if success:
        print("\n✅ BrowserMCP basic functionality works!")
    else:
        print("\n❌ BrowserMCP test failed")
    
    return success

if __name__ == "__main__":
    main()