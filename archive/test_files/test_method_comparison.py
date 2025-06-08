#!/usr/bin/env python3
"""
Extraction Method Comparison Framework

Compares BrowserMCP vs Selenium approaches for Instagram carousel extraction
and identifies the optimal implementation strategy.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import test implementations
from test_browsermcp_carousel_extractor import BrowserMCPCarouselExtractor
from test_selenium_carousel_extractor import SeleniumCarouselExtractor
from carousel_test_plan import TEST_SHORTCODES, SUCCESS_CRITERIA

class ExtractionMethodComparator:
    """Compares different extraction methods and analyzes performance"""
    
    def __init__(self):
        self.results = {}
        
    async def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run both methods and compare results"""
        print("🔬 EXTRACTION METHOD COMPARISON")
        print("=" * 60)
        
        comparison_results = {
            "timestamp": datetime.now().isoformat(),
            "test_shortcodes": list(TEST_SHORTCODES.keys()),
            "methods": {}
        }
        
        # Test Selenium method
        print("\n📍 Testing Selenium Enhanced Method...")
        selenium_extractor = SeleniumCarouselExtractor()
        selenium_results = selenium_extractor.run_comprehensive_test()
        comparison_results["methods"]["selenium"] = selenium_results
        
        # Test BrowserMCP method (simulated)
        print("\n📍 Testing BrowserMCP Method...")
        browsermcp_extractor = BrowserMCPCarouselExtractor()
        browsermcp_results = await browsermcp_extractor.run_comprehensive_test()
        comparison_results["methods"]["browsermcp"] = browsermcp_results
        
        # Analyze and compare
        analysis = self.analyze_method_performance(comparison_results)
        comparison_results["analysis"] = analysis
        
        # Generate recommendations
        recommendations = self.generate_recommendations(analysis)
        comparison_results["recommendations"] = recommendations
        
        return comparison_results
    
    def analyze_method_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics for each method"""
        print("\n📊 Analyzing method performance...")
        
        analysis = {
            "accuracy_comparison": {},
            "performance_comparison": {},
            "reliability_comparison": {},
            "feature_comparison": {},
            "detailed_breakdown": {}
        }
        
        methods = results["methods"]
        
        # Accuracy Analysis
        for method_name, method_results in methods.items():
            if "error" in method_results:
                analysis["accuracy_comparison"][method_name] = {
                    "accuracy_rate": 0,
                    "successful_tests": 0,
                    "total_tests": 0,
                    "error": method_results["error"]
                }
                continue
            
            accuracy_rate = method_results.get("accuracy_rate", 0)
            successful_tests = method_results.get("successful_tests", 0)
            total_tests = method_results.get("total_tests", 0)
            
            analysis["accuracy_comparison"][method_name] = {
                "accuracy_rate": accuracy_rate,
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "meets_target": accuracy_rate >= 95  # From SUCCESS_CRITERIA
            }
        
        # Performance Analysis
        for method_name, method_results in methods.items():
            if "error" in method_results:
                continue
                
            avg_duration = method_results.get("average_duration", 0)
            individual_results = method_results.get("individual_results", {})
            
            # Calculate performance metrics
            durations = [r.get("duration_seconds", 0) for r in individual_results.values() 
                        if "duration_seconds" in r]
            
            analysis["performance_comparison"][method_name] = {
                "average_duration": avg_duration,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "meets_speed_target": avg_duration <= 15  # From SUCCESS_CRITERIA
            }
        
        # Reliability Analysis
        for method_name, method_results in methods.items():
            if "error" in method_results:
                analysis["reliability_comparison"][method_name] = {
                    "setup_success": False,
                    "error_rate": 100,
                    "common_errors": [method_results["error"]]
                }
                continue
                
            individual_results = method_results.get("individual_results", {})
            
            # Analyze error patterns
            errors = []
            successful_count = 0
            
            for shortcode, result in individual_results.items():
                if result.get("success", False):
                    successful_count += 1
                else:
                    error = result.get("error", "Unknown error")
                    errors.append(f"{shortcode}: {error}")
            
            error_rate = ((len(individual_results) - successful_count) / len(individual_results) * 100) if individual_results else 100
            
            analysis["reliability_comparison"][method_name] = {
                "setup_success": True,
                "error_rate": error_rate,
                "common_errors": errors,
                "meets_reliability_target": error_rate <= 10  # 90% success rate target
            }
        
        # Feature Comparison
        feature_matrix = {
            "selenium": {
                "popup_handling": "Comprehensive",
                "carousel_detection": "Multi-method",
                "navigation_methods": "4 fallback methods",
                "anti_detection": "Advanced stealth",
                "image_filtering": "Date-based + smart",
                "deduplication": "URL pattern + hash",
                "error_recovery": "Extensive",
                "browser_compatibility": "Excellent",
                "setup_complexity": "Low",
                "maintenance_burden": "Low"
            },
            "browsermcp": {
                "popup_handling": "Advanced",
                "carousel_detection": "Multi-indicator",
                "navigation_methods": "3 fallback methods",
                "anti_detection": "Built-in",
                "image_filtering": "Carousel-aware",
                "deduplication": "Hash-based",
                "error_recovery": "Good",
                "browser_compatibility": "Good",
                "setup_complexity": "Medium",
                "maintenance_burden": "Medium"
            }
        }
        
        analysis["feature_comparison"] = feature_matrix
        
        # Detailed Breakdown by Test Case
        for method_name, method_results in methods.items():
            if "error" in method_results:
                continue
                
            individual_results = method_results.get("individual_results", {})
            breakdown = {}
            
            for shortcode, result in individual_results.items():
                test_info = TEST_SHORTCODES.get(shortcode, {})
                expected = test_info.get("expected_images", 1)
                actual = result.get("extracted_images", 0)
                
                breakdown[shortcode] = {
                    "test_type": test_info.get("type", "unknown"),
                    "expected_images": expected,
                    "extracted_images": actual,
                    "accuracy": "correct" if actual == expected else "incorrect",
                    "carousel_detected": result.get("carousel_detected", False),
                    "duration": result.get("duration_seconds", 0),
                    "error": result.get("error")
                }
            
            analysis["detailed_breakdown"][method_name] = breakdown
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analysis"""
        print("💡 Generating recommendations...")
        
        recommendations = {
            "primary_method": None,
            "hybrid_approach": {},
            "implementation_priorities": [],
            "risk_mitigation": [],
            "next_steps": []
        }
        
        accuracy_comparison = analysis["accuracy_comparison"]
        performance_comparison = analysis["performance_comparison"]
        reliability_comparison = analysis["reliability_comparison"]
        
        # Determine primary method
        method_scores = {}
        
        for method in ["selenium", "browsermcp"]:
            score = 0
            
            # Accuracy weight (40%)
            if method in accuracy_comparison:
                accuracy = accuracy_comparison[method].get("accuracy_rate", 0)
                score += (accuracy / 100) * 0.4
            
            # Performance weight (20%) 
            if method in performance_comparison:
                perf = performance_comparison[method]
                speed_score = 1.0 if perf.get("meets_speed_target", False) else 0.5
                score += speed_score * 0.2
            
            # Reliability weight (40%)
            if method in reliability_comparison:
                rel = reliability_comparison[method]
                reliability_score = 1.0 if rel.get("meets_reliability_target", False) else 0.3
                score += reliability_score * 0.4
            
            method_scores[method] = score
        
        # Select primary method
        if method_scores:
            primary_method = max(method_scores.keys(), key=lambda k: method_scores[k])
            recommendations["primary_method"] = {
                "method": primary_method,
                "score": method_scores[primary_method],
                "confidence": "high" if method_scores[primary_method] > 0.8 else "medium"
            }
        
        # Hybrid approach recommendations
        selenium_accuracy = accuracy_comparison.get("selenium", {}).get("accuracy_rate", 0)
        browsermcp_accuracy = accuracy_comparison.get("browsermcp", {}).get("accuracy_rate", 0)
        
        if selenium_accuracy > 80 and browsermcp_accuracy > 80:
            recommendations["hybrid_approach"] = {
                "feasible": True,
                "strategy": "Use Selenium as primary, BrowserMCP for complex cases",
                "implementation": {
                    "primary": "selenium",
                    "fallback": "browsermcp", 
                    "triggers": ["navigation_failure", "complex_carousel", "anti_detection_needed"]
                }
            }
        elif selenium_accuracy > browsermcp_accuracy:
            recommendations["hybrid_approach"] = {
                "feasible": False,
                "reason": "Selenium significantly outperforms BrowserMCP",
                "recommendation": "Focus on Selenium optimization"
            }
        else:
            recommendations["hybrid_approach"] = {
                "feasible": False,
                "reason": "BrowserMCP significantly outperforms Selenium",
                "recommendation": "Focus on BrowserMCP optimization"
            }
        
        # Implementation priorities
        priorities = [
            "Implement robust popup handling (highest accuracy impact)",
            "Perfect carousel navigation with multiple fallbacks",
            "Optimize image filtering for date-based grouping",
            "Add comprehensive error recovery mechanisms",
            "Implement advanced deduplication algorithms"
        ]
        
        # Add method-specific priorities
        if recommendations["primary_method"]["method"] == "selenium":
            priorities.extend([
                "Enhance anti-detection capabilities",
                "Optimize browser setup for stealth mode",
                "Add rate limiting for Instagram compliance"
            ])
        else:
            priorities.extend([
                "Integrate BrowserMCP advanced features",
                "Optimize async/await patterns",
                "Add browser state management"
            ])
        
        recommendations["implementation_priorities"] = priorities
        
        # Risk mitigation
        recommendations["risk_mitigation"] = [
            "Implement comprehensive error logging for debugging",
            "Add retry mechanisms with exponential backoff",
            "Create fallback extraction methods for edge cases",
            "Monitor Instagram layout changes proactively",
            "Add performance monitoring and alerting",
            "Implement rate limiting to avoid IP blocking"
        ]
        
        # Next steps
        recommendations["next_steps"] = [
            "Implement the recommended primary method",
            "Create comprehensive test suite for regression testing",
            "Set up continuous monitoring of extraction accuracy",
            "Plan for Instagram layout change adaptation",
            "Document all edge cases and handling strategies",
            "Create production deployment and monitoring strategy"
        ]
        
        return recommendations
    
    def print_comparison_summary(self, results: Dict[str, Any]):
        """Print formatted comparison summary"""
        print("\n" + "=" * 60)
        print("📋 EXTRACTION METHOD COMPARISON SUMMARY")
        print("=" * 60)
        
        analysis = results.get("analysis", {})
        recommendations = results.get("recommendations", {})
        
        # Accuracy Summary
        print("\n🎯 ACCURACY COMPARISON:")
        accuracy_comp = analysis.get("accuracy_comparison", {})
        for method, stats in accuracy_comp.items():
            accuracy = stats.get("accuracy_rate", 0)
            success_count = stats.get("successful_tests", 0)
            total_count = stats.get("total_tests", 0)
            meets_target = "✅" if stats.get("meets_target", False) else "❌"
            
            print(f"   {method.upper()}: {accuracy:.1f}% ({success_count}/{total_count}) {meets_target}")
        
        # Performance Summary  
        print("\n⚡ PERFORMANCE COMPARISON:")
        perf_comp = analysis.get("performance_comparison", {})
        for method, stats in perf_comp.items():
            avg_duration = stats.get("average_duration", 0)
            meets_target = "✅" if stats.get("meets_speed_target", False) else "❌"
            
            print(f"   {method.upper()}: {avg_duration:.1f}s average {meets_target}")
        
        # Reliability Summary
        print("\n🛡️ RELIABILITY COMPARISON:")
        rel_comp = analysis.get("reliability_comparison", {})
        for method, stats in rel_comp.items():
            error_rate = stats.get("error_rate", 100)
            meets_target = "✅" if stats.get("meets_reliability_target", False) else "❌"
            
            print(f"   {method.upper()}: {error_rate:.1f}% error rate {meets_target}")
        
        # Recommendation
        print("\n💡 RECOMMENDATION:")
        primary = recommendations.get("primary_method", {})
        if primary:
            method = primary.get("method", "").upper()
            score = primary.get("score", 0)
            confidence = primary.get("confidence", "unknown")
            
            print(f"   Primary Method: {method}")
            print(f"   Overall Score: {score:.2f}/1.00")
            print(f"   Confidence: {confidence}")
        
        # Next Steps
        next_steps = recommendations.get("next_steps", [])
        if next_steps:
            print(f"\n🚀 NEXT STEPS:")
            for i, step in enumerate(next_steps[:3], 1):
                print(f"   {i}. {step}")

async def main():
    """Main comparison execution"""
    comparator = ExtractionMethodComparator()
    
    print("🎬 Starting comprehensive extraction method comparison...")
    print("This will test both Selenium and BrowserMCP approaches")
    
    try:
        results = await comparator.run_comprehensive_comparison()
        
        # Save detailed results
        Path("test_results").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"test_results/method_comparison_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        comparator.print_comparison_summary(results)
        
        print(f"\n💾 Detailed results saved to test_results/method_comparison_{timestamp}.json")
        
        # Final recommendation
        recommendations = results.get("recommendations", {})
        primary_method = recommendations.get("primary_method", {})
        
        if primary_method and primary_method.get("score", 0) > 0.8:
            method = primary_method.get("method", "").upper()
            print(f"\n🎉 CLEAR WINNER: {method} method recommended for production")
        elif primary_method:
            method = primary_method.get("method", "").upper()
            print(f"\n🤔 CAUTIOUS RECOMMENDATION: {method} method with optimizations needed")
        else:
            print(f"\n⚠️  NO CLEAR WINNER: Consider hybrid approach or further development")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())