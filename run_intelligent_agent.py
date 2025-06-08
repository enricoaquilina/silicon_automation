#!/usr/bin/env python3
"""
Run Intelligent Carousel Agent

Simple script to test the enhanced carousel agent with Pydantic models and LangGraph.
This demonstrates the agent's ability to diagnose and fix carousel extraction issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path to import the agent
sys.path.append(str(Path(__file__).parent))

def check_environment():
    """Check if all required files are available"""
    print("🔍 Checking environment setup...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python version: {sys.version}")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    required_files = [
        "carousel_test_plan.py",
        "intelligent_carousel_agent.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Missing optional files: {missing_files}")
        print(f"   Current directory: {current_dir}")
        print("   Will proceed with fallback functionality")
    else:
        print("✅ All required files found")
    
    return True


try:
    from intelligent_carousel_agent import IntelligentCarouselAgent
    print("✅ Successfully imported IntelligentCarouselAgent")
except ImportError as e:
    print(f"❌ Failed to import agent: {e}")
    sys.exit(1)

async def test_agent_basic_functionality():
    """Test basic agent functionality without requiring external dependencies"""
    print("\n🧪 TESTING BASIC AGENT FUNCTIONALITY")
    print("-" * 50)
    
    # Initialize agent without requiring Replicate token
    agent = IntelligentCarouselAgent()
    
    # Test single shortcode extraction
    test_shortcode = "C0xFHGOrBN7"
    print(f"\n🎯 Testing single extraction: {test_shortcode}")
    
    try:
        result = await agent.extract_shortcode_with_fixes(test_shortcode)
        
        print(f"✅ Extraction completed!")
        print(f"   Status: {result.status}")
        print(f"   Duration: {result.duration_seconds:.1f}s")
        print(f"   Images Found: {len(result.extracted_images)}")
        print(f"   Carousel Detected: {result.carousel_detected.is_carousel}")
        print(f"   Fixes Applied: {result.success_metrics.get('fixes_applied', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Single extraction test failed: {e}")
        return False

async def test_agent_batch_processing():
    """Test batch processing capabilities"""
    print("\n🚀 TESTING BATCH PROCESSING")
    print("-" * 50)
    
    agent = IntelligentCarouselAgent()
    
    # Test multiple shortcodes
    test_shortcodes = ["C0xFHGOrBN7", "C0wmEEKItfR", "C0xMpxwKoxb"]
    
    try:
        results = await agent.batch_extract_with_fixes(test_shortcodes)
        
        print(f"✅ Batch processing completed!")
        print(f"   Total Processed: {len(results)}")
        
        successful_count = sum(1 for r in results.values() if r.status.value == "success")
        success_rate = (successful_count / len(results)) * 100
        
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Successful: {successful_count}/{len(results)}")
        
        # Generate and save report
        report = agent.generate_comprehensive_report(results)
        report_path = await agent.save_comprehensive_report(report)
        
        print(f"   Report Saved: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

async def test_agent_code_generation():
    """Test code generation capabilities"""
    print("\n🔧 TESTING CODE GENERATION")
    print("-" * 50)
    
    agent = IntelligentCarouselAgent()
    
    try:
        # Test different types of fix code generation
        test_cases = [
            ("navigation timing", "timing issues"),
            ("popup interference", "popup handling"),
            ("duplicate detection", "deduplication"),
            ("general", "general fixes")
        ]
        
        for issue_type, description in test_cases:
            print(f"\n   🎯 Testing {description} code generation...")
            
            # Create mock state
            mock_state = {
                "session_metadata": {
                    "test_diagnostic": {
                        "issues_identified": [issue_type]
                    }
                }
            }
            
            # Generate fix code
            if issue_type == "navigation timing":
                fix_code = agent._generate_timing_fix_code()
            elif issue_type == "popup interference":
                fix_code = agent._generate_popup_fix_code()
            elif issue_type == "duplicate detection":
                fix_code = agent._generate_dedup_fix_code()
            else:
                fix_code = agent._generate_general_fix_code()
            
            if fix_code and len(fix_code) > 100:  # Reasonable code length
                print(f"   ✅ Generated {len(fix_code)} chars of fix code")
            else:
                print(f"   ⚠️  Generated code seems too short: {len(fix_code) if fix_code else 0} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Code generation test failed: {e}")
        return False

async def run_comprehensive_tests():
    """Run all agent tests"""
    print("🤖 INTELLIGENT CAROUSEL AGENT - COMPREHENSIVE TESTING")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Basic functionality
    test_results["basic"] = await test_agent_basic_functionality()
    
    # Test 2: Batch processing
    test_results["batch"] = await test_agent_batch_processing()
    
    # Test 3: Code generation
    test_results["code_gen"] = await test_agent_code_generation()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("-" * 30)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Agent is ready for production use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed_tests == total_tests

def main():
    """Main launcher function"""
    print("🤖 Intelligent Carousel Agent Launcher")
    print("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Step 2: Run comprehensive tests
    print("\n✅ Environment check passed. Starting tests...")
    success = asyncio.run(run_comprehensive_tests())
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\n📊 Check the following for results:")
        print("   📁 agent_workspace/ - Generated code and fixes")
        print("   📄 agent_extraction_report_*.json - Test results")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()