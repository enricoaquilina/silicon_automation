#!/usr/bin/env python3
"""
Test Intelligent Agent with Real Browser Automation

This tests the intelligent agent against C0xFHGOrBN7 specifically to see if it can
extract all 3 carousel images using real BrowserMCP tools.
"""

import asyncio
import time
from intelligent_carousel_agent import IntelligentCarouselAgent


async def test_c0xfhgorbN7_real_extraction():
    """
    Test real extraction of C0xFHGOrBN7 (3-image carousel)
    This should extract all 3 images if the agent is working properly
    """
    print("🧪 TESTING INTELLIGENT AGENT ON C0xFHGOrBN7")
    print("=" * 60)
    print("Target: 3-image carousel")
    print("Expected: 3 images extracted")
    print("Previous results: Only 1/3 images extracted")
    print()
    
    # Create agent instance
    agent = IntelligentCarouselAgent()
    
    # Test single shortcode extraction
    start_time = time.time()
    result = await agent.extract_shortcode_with_intelligence("C0xFHGOrBN7")
    duration = time.time() - start_time
    
    # Analyze results
    print("\n📊 TEST RESULTS:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Expected Images: {result.get('expected_images', 'unknown')}")
    print(f"   Extracted Images: {result.get('extracted_images', 0)}")
    print(f"   Strategy Used: {result.get('strategy_used', 'unknown')}")
    print(f"   Duration: {duration:.1f}s")
    
    if result.get('downloaded_images'):
        print(f"   Downloaded Files:")
        for img in result['downloaded_images']:
            print(f"     - {img['filename']}")
    
    # Check if improvement occurred
    expected = 3
    extracted = result.get('extracted_images', 0)
    
    if extracted >= expected:
        print("\n🎉 SUCCESS! Agent successfully extracted all carousel images!")
        print("✅ Improvement: 100% extraction rate")
    elif extracted > 1:
        print(f"\n📈 PARTIAL IMPROVEMENT: {extracted}/3 images extracted")
        print(f"✅ Improvement: {(extracted/expected)*100:.1f}% vs previous ~33%")
    else:
        print("\n⚠️ NO IMPROVEMENT: Still only getting 1/3 images")
        print("🔧 Agent needs further optimization")
    
    # Show learning data
    print(f"\n🧠 LEARNING DATA:")
    print(f"   Strategy Success Rate: {agent.strategy_success_rates}")
    print(f"   Shortcode Learning: {agent.shortcode_specific_learning.get('C0xFHGOrBN7', {})}")
    
    return result


async def test_navigation_methods():
    """
    Test different navigation methods specifically
    """
    print("\n🎠 TESTING NAVIGATION METHODS")
    print("-" * 40)
    
    agent = IntelligentCarouselAgent()
    
    # Simulate navigation to the post first
    await agent._intelligent_navigation("C0xFHGOrBN7")
    
    # Test each navigation method
    from intelligent_carousel_agent import NavigationMethod
    
    methods = [
        NavigationMethod.BUTTON_CLICK,
        NavigationMethod.KEYBOARD_ARROW,
        NavigationMethod.TOUCH_SWIPE,
        NavigationMethod.JAVASCRIPT_TRANSFORM
    ]
    
    results = {}
    
    for method in methods:
        print(f"Testing {method.value}...")
        try:
            success = await agent._try_navigation_method(method)
            results[method.value] = success
            print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
        except Exception as e:
            results[method.value] = False
            print(f"  Result: ❌ Error: {e}")
    
    print(f"\n📊 Navigation Results: {results}")
    working_methods = [k for k, v in results.items() if v]
    print(f"✅ Working methods: {working_methods}")
    
    return results


if __name__ == "__main__":
    async def main():
        # Test real extraction
        extraction_result = await test_c0xfhgorbN7_real_extraction()
        
        # Test navigation methods
        navigation_result = await test_navigation_methods()
        
        # Final summary
        print("\n" + "="*60)
        print("🏁 FINAL TEST SUMMARY")
        print("="*60)
        
        success = extraction_result.get('success', False)
        extracted = extraction_result.get('extracted_images', 0)
        
        if success and extracted >= 3:
            print("🎉 AGENT WORKING PERFECTLY!")
            print("   ✅ All carousel images extracted")
            print("   ✅ Target success criteria met")
        elif extracted > 1:
            print("📈 AGENT SHOWING IMPROVEMENT!")
            print(f"   ✅ Extracted {extracted}/3 images")
            print("   🔧 Further optimization possible")
        else:
            print("⚠️ AGENT NEEDS MORE WORK")
            print("   ❌ Still not extracting full carousel")
            print("   🔧 Navigation or strategy issues remain")
        
        working_nav = len([k for k, v in navigation_result.items() if v])
        print(f"\n🎠 Navigation: {working_nav}/4 methods working")
        
        return {
            'extraction': extraction_result,
            'navigation': navigation_result
        }
    
    # Run the test
    asyncio.run(main())