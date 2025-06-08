#!/usr/bin/env python3
"""
Intelligent Model Orchestrator Agent
- Routes generations to optimal models based on content analysis, budget, and quality requirements
- Learns from performance data to improve routing decisions
- Balances cost vs quality for different content types
- Implements fallback strategies and retry logic
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentType(Enum):
    HERO_POST = "hero_post"          # Top performing, maximum quality needed
    PREMIUM_CONTENT = "premium"      # High-quality posts, proven models
    STANDARD_CONTENT = "standard"    # Regular posts, balance cost/quality  
    BULK_CONTENT = "bulk"           # High volume, cost-optimized
    EXPERIMENTAL = "experimental"    # Testing new models/approaches


class BudgetTier(Enum):
    ULTRA_LOW = "ultra_low"     # <$0.10 per generation
    LOW = "low"                 # $0.10-$0.50 per generation  
    MEDIUM = "medium"           # $0.50-$2.00 per generation
    HIGH = "high"               # $2.00-$5.00 per generation
    PREMIUM = "premium"         # >$5.00 per generation


@dataclass
class ModelConfig:
    """Configuration for a specific AI model"""
    model_id: str
    version: str
    cost_per_generation: float
    avg_generation_time: float
    success_rate: float
    quality_score: float  # 1-10 based on historical results
    supported_features: List[str]
    budget_tier: BudgetTier
    content_suitability: List[ContentType]
    reliability_score: float  # 1-10 based on uptime/errors


@dataclass 
class GenerationRequest:
    """Request for content generation"""
    content_type: ContentType
    budget_constraint: BudgetTier
    quality_requirement: float  # 1-10 minimum quality needed
    features_required: List[str]
    priority: int  # 1-10, higher = more important
    fallback_allowed: bool = True
    max_retries: int = 3


class IntelligentModelOrchestrator:
    """Intelligent agent that routes generations to optimal models"""
    
    def __init__(self):
        self.models = self._initialize_model_catalog()
        self.performance_history = {}
        self.routing_decisions = []
        self.budget_tracking = {
            "daily_spend": 0.0,
            "monthly_spend": 0.0,
            "daily_limit": 50.0,  # $50/day default
            "monthly_limit": 1000.0  # $1000/month default
        }
        
    def _initialize_model_catalog(self) -> Dict[str, ModelConfig]:
        """Initialize catalog of available models with current data"""
        
        return {
            # ULTRA-CHEAP IMAGE-TO-VIDEO MODELS
            "luma-ray-flash-2": ModelConfig(
                model_id="luma-ray-flash-2",
                version="95ab790a8dd6d5a0a3527cb6c9a0b22a8b3f2ce8fef23ae60d5dc6a1ad8ba6af",
                cost_per_generation=0.022,
                avg_generation_time=120.0,
                success_rate=0.85,  # Estimated, needs validation
                quality_score=6.0,  # Unknown, needs testing
                supported_features=["image-to-video", "720p", "5s"],
                budget_tier=BudgetTier.ULTRA_LOW,
                content_suitability=[ContentType.BULK_CONTENT, ContentType.EXPERIMENTAL],
                reliability_score=7.0  # Estimated
            ),
            
            "leonardo-motion-2": ModelConfig(
                model_id="leonardo-motion-2", 
                version="3a2633c4fc40d3b76c0cf31c9b859ff3f6a9f524972365c3c868f99ba90ee70d",
                cost_per_generation=0.025,
                avg_generation_time=90.0,
                success_rate=0.90,  # Estimated
                quality_score=7.0,  # Unknown, needs testing
                supported_features=["image-to-video", "480p", "5s", "style-options"],
                budget_tier=BudgetTier.ULTRA_LOW,
                content_suitability=[ContentType.BULK_CONTENT, ContentType.STANDARD_CONTENT],
                reliability_score=8.0
            ),
            
            # PROVEN RELIABLE MODELS
            "kling-v2": ModelConfig(
                model_id="kling-v2",
                version="03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                cost_per_generation=1.40,
                avg_generation_time=229.0,  # From test results
                success_rate=1.0,  # 100% success in tests
                quality_score=8.5,  # Proven good quality
                supported_features=["image-to-video", "720p", "5s", "reliable"],
                budget_tier=BudgetTier.MEDIUM,
                content_suitability=[ContentType.PREMIUM_CONTENT, ContentType.HERO_POST],
                reliability_score=9.5
            ),
            
            "hunyuan-video": ModelConfig(
                model_id="hunyuan-video",
                version="6c9132aee14409cd6568d030453f1ba50f5f3412b844fe67f78a9eb62d55664f", 
                cost_per_generation=2.02,
                avg_generation_time=318.0,  # From test results
                success_rate=1.0,  # 100% success in tests
                quality_score=9.0,  # State-of-the-art
                supported_features=["text-to-video", "realistic-motion", "5.4s"],
                budget_tier=BudgetTier.MEDIUM,
                content_suitability=[ContentType.HERO_POST, ContentType.PREMIUM_CONTENT],
                reliability_score=9.0
            ),
            
            # PREMIUM MODELS (expensive but highest quality)
            "google-veo-3": ModelConfig(
                model_id="google-veo-3",
                version="b8c0088ae1b8b4b9c24b57c68a6db3af7c1a5e5",  # Example
                cost_per_generation=6.00,
                avg_generation_time=142.0,  # From test results
                success_rate=1.0,
                quality_score=9.5,  # Premium quality
                supported_features=["text-to-video", "8s", "audio", "premium"],
                budget_tier=BudgetTier.PREMIUM,
                content_suitability=[ContentType.HERO_POST],
                reliability_score=9.0
            )
        }
    
    def analyze_content_requirements(self, request: GenerationRequest) -> Dict[str, Any]:
        """Analyze what the content requires and suggest optimal routing"""
        
        analysis = {
            "content_type": request.content_type,
            "budget_constraint": request.budget_constraint,
            "quality_requirement": request.quality_requirement,
            "features_required": request.features_required,
            "priority": request.priority
        }
        
        # Content type specific requirements
        if request.content_type == ContentType.HERO_POST:
            analysis["min_quality_score"] = 8.5
            analysis["min_reliability"] = 9.0
            analysis["max_cost"] = 6.00
            
        elif request.content_type == ContentType.PREMIUM_CONTENT:
            analysis["min_quality_score"] = 7.5
            analysis["min_reliability"] = 8.0
            analysis["max_cost"] = 2.50
            
        elif request.content_type == ContentType.STANDARD_CONTENT:
            analysis["min_quality_score"] = 6.0
            analysis["min_reliability"] = 7.0
            analysis["max_cost"] = 1.50
            
        elif request.content_type == ContentType.BULK_CONTENT:
            analysis["min_quality_score"] = 5.0
            analysis["min_reliability"] = 6.0
            analysis["max_cost"] = 0.10
            
        return analysis
    
    def score_model_for_request(self, model: ModelConfig, analysis: Dict[str, Any]) -> float:
        """Score how well a model matches the request requirements"""
        
        score = 0.0
        
        # Quality match (30% weight)
        quality_match = min(model.quality_score / analysis.get("min_quality_score", 5.0), 1.0)
        score += quality_match * 0.30
        
        # Cost efficiency (25% weight)
        max_cost = analysis.get("max_cost", 10.0)
        if model.cost_per_generation <= max_cost:
            cost_efficiency = (max_cost - model.cost_per_generation) / max_cost
            score += cost_efficiency * 0.25
        
        # Reliability (20% weight)
        reliability_match = min(model.reliability_score / analysis.get("min_reliability", 5.0), 1.0)
        score += reliability_match * 0.20
        
        # Success rate (15% weight)
        score += model.success_rate * 0.15
        
        # Speed (generation time, 10% weight)
        # Faster is better, normalize against 300s baseline
        speed_score = max(0, 1 - (model.avg_generation_time / 300.0))
        score += speed_score * 0.10
        
        return score
    
    def route_generation_request(self, request: GenerationRequest) -> Tuple[ModelConfig, List[ModelConfig]]:
        """Route generation request to optimal model with fallbacks"""
        
        # Analyze requirements
        analysis = self.analyze_content_requirements(request)
        
        # Filter eligible models
        eligible_models = []
        for model in self.models.values():
            # Check content suitability (allow experimental for all, and flexible matching)
            if request.content_type != ContentType.EXPERIMENTAL:
                # For non-experimental, allow if either exact match OR if model supports higher tiers
                content_hierarchy = [ContentType.BULK_CONTENT, ContentType.STANDARD_CONTENT, 
                                   ContentType.PREMIUM_CONTENT, ContentType.HERO_POST]
                if request.content_type in content_hierarchy:
                    request_level = content_hierarchy.index(request.content_type)
                    model_max_level = max([content_hierarchy.index(ct) for ct in model.content_suitability 
                                         if ct in content_hierarchy], default=-1)
                    if model_max_level < request_level:
                        continue
                
            # Check budget constraint
            if model.budget_tier.value != request.budget_constraint.value:
                # Allow lower-cost tiers if budget permits
                budget_order = [BudgetTier.ULTRA_LOW, BudgetTier.LOW, BudgetTier.MEDIUM, BudgetTier.HIGH, BudgetTier.PREMIUM]
                model_budget_idx = budget_order.index(model.budget_tier)
                request_budget_idx = budget_order.index(request.budget_constraint)
                if model_budget_idx > request_budget_idx:
                    continue
            
            # Check required features
            if not all(feature in model.supported_features for feature in request.features_required):
                continue
                
            # Check quality requirements
            if model.quality_score < request.quality_requirement:
                continue
                
            eligible_models.append(model)
        
        if not eligible_models:
            raise ValueError(f"No models found matching requirements: {analysis}")
        
        # Score and rank models
        scored_models = []
        for model in eligible_models:
            score = self.score_model_for_request(model, analysis)
            scored_models.append((score, model))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[0], reverse=True)
        
        primary_model = scored_models[0][1]
        fallback_models = [model for _, model in scored_models[1:3]]  # Top 2 fallbacks
        
        # Log routing decision
        routing_decision = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "content_type": request.content_type.value,
                "budget_constraint": request.budget_constraint.value,
                "quality_requirement": request.quality_requirement
            },
            "primary_model": primary_model.model_id,
            "primary_score": scored_models[0][0],
            "fallback_models": [m.model_id for m in fallback_models],
            "analysis": analysis
        }
        
        self.routing_decisions.append(routing_decision)
        
        logger.info(f"Routed {request.content_type.value} to {primary_model.model_id} (score: {scored_models[0][0]:.3f})")
        
        return primary_model, fallback_models
    
    def get_cost_optimization_strategy(self, total_posts: int = 2639) -> Dict[str, Any]:
        """Generate cost optimization strategy for Instagram database"""
        
        # Content distribution (based on importance analysis)
        distribution = {
            ContentType.HERO_POST: 50,        # Top 2% - maximum quality
            ContentType.PREMIUM_CONTENT: 200,  # Top 8% - high quality
            ContentType.STANDARD_CONTENT: 800, # 30% - balanced
            ContentType.BULK_CONTENT: 1589     # 60% - cost optimized
        }
        
        strategies = {
            "ultra_conservative": {
                "description": "Maximum cost savings - test cheap models extensively",
                "routing": {
                    ContentType.HERO_POST: "kling-v2",
                    ContentType.PREMIUM_CONTENT: "leonardo-motion-2", 
                    ContentType.STANDARD_CONTENT: "luma-ray-flash-2",
                    ContentType.BULK_CONTENT: "luma-ray-flash-2"
                },
                "estimated_cost": self._calculate_strategy_cost(distribution, {
                    ContentType.HERO_POST: 1.40,
                    ContentType.PREMIUM_CONTENT: 0.025,
                    ContentType.STANDARD_CONTENT: 0.022,
                    ContentType.BULK_CONTENT: 0.022
                })
            },
            
            "balanced_intelligent": {
                "description": "AI-routed decisions with cost awareness",
                "routing": {
                    ContentType.HERO_POST: "hunyuan-video",
                    ContentType.PREMIUM_CONTENT: "kling-v2",
                    ContentType.STANDARD_CONTENT: "leonardo-motion-2",
                    ContentType.BULK_CONTENT: "luma-ray-flash-2"
                },
                "estimated_cost": self._calculate_strategy_cost(distribution, {
                    ContentType.HERO_POST: 2.02,
                    ContentType.PREMIUM_CONTENT: 1.40,
                    ContentType.STANDARD_CONTENT: 0.025,
                    ContentType.BULK_CONTENT: 0.022
                })
            },
            
            "quality_first": {
                "description": "Quality prioritized with intelligent fallbacks",
                "routing": {
                    ContentType.HERO_POST: "google-veo-3",
                    ContentType.PREMIUM_CONTENT: "hunyuan-video",
                    ContentType.STANDARD_CONTENT: "kling-v2", 
                    ContentType.BULK_CONTENT: "leonardo-motion-2"
                },
                "estimated_cost": self._calculate_strategy_cost(distribution, {
                    ContentType.HERO_POST: 6.00,
                    ContentType.PREMIUM_CONTENT: 2.02,
                    ContentType.STANDARD_CONTENT: 1.40,
                    ContentType.BULK_CONTENT: 0.025
                })
            }
        }
        
        return {
            "content_distribution": {k.value: v for k, v in distribution.items()},
            "strategies": strategies,
            "recommendation": "Start with ultra_conservative to validate cheap models, then upgrade to balanced_intelligent"
        }
    
    def _calculate_strategy_cost(self, distribution: Dict[ContentType, int], costs: Dict[ContentType, float]) -> float:
        """Calculate total cost for a strategy"""
        total = 0.0
        for content_type, count in distribution.items():
            total += count * costs.get(content_type, 0.0)
        return total
    
    async def execute_generation_with_fallbacks(self, request: GenerationRequest, **kwargs) -> Dict[str, Any]:
        """Execute generation with intelligent routing and fallbacks"""
        
        primary_model, fallback_models = self.route_generation_request(request)
        
        models_to_try = [primary_model] + fallback_models
        
        for attempt, model in enumerate(models_to_try):
            try:
                logger.info(f"Attempt {attempt + 1}: Using {model.model_id}")
                
                # Check budget constraints
                if self.budget_tracking["daily_spend"] + model.cost_per_generation > self.budget_tracking["daily_limit"]:
                    logger.warning(f"Daily budget limit would be exceeded with {model.model_id}")
                    continue
                
                # Execute generation (placeholder - would call actual API)
                result = await self._execute_model_generation(model, **kwargs)
                
                if result["success"]:
                    # Update budget tracking
                    self.budget_tracking["daily_spend"] += model.cost_per_generation
                    self.budget_tracking["monthly_spend"] += model.cost_per_generation
                    
                    # Record performance
                    self._record_performance(model, result, success=True)
                    
                    logger.info(f"✅ Success with {model.model_id} - Cost: ${model.cost_per_generation:.3f}")
                    
                    return {
                        "success": True,
                        "model_used": model.model_id,
                        "attempt": attempt + 1,
                        "cost": model.cost_per_generation,
                        "result": result
                    }
                
            except Exception as e:
                logger.error(f"❌ {model.model_id} failed: {str(e)}")
                self._record_performance(model, None, success=False, error=str(e))
                continue
        
        return {
            "success": False,
            "error": "All models failed",
            "models_tried": [m.model_id for m in models_to_try]
        }
    
    async def _execute_model_generation(self, model: ModelConfig, **kwargs) -> Dict[str, Any]:
        """Execute actual model generation (placeholder)"""
        # This would contain the actual API calls to different models
        # For now, simulate based on model reliability
        
        import random
        await asyncio.sleep(2)  # Simulate generation time
        
        if random.random() < model.success_rate:
            return {
                "success": True,
                "output": f"Generated content using {model.model_id}",
                "generation_time": model.avg_generation_time + random.uniform(-30, 30)
            }
        else:
            return {
                "success": False,
                "error": "Simulated model failure"
            }
    
    def _record_performance(self, model: ModelConfig, result: Optional[Dict], success: bool, error: str = None):
        """Record model performance for learning"""
        
        if model.model_id not in self.performance_history:
            self.performance_history[model.model_id] = []
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error": error,
            "generation_time": result.get("generation_time") if result else None
        }
        
        self.performance_history[model.model_id].append(record)
        
        # Update model success rate based on recent performance
        recent_records = self.performance_history[model.model_id][-20:]  # Last 20 attempts
        if len(recent_records) >= 5:
            recent_success_rate = sum(1 for r in recent_records if r["success"]) / len(recent_records)
            # Weighted average: 70% historical, 30% recent
            self.models[model.model_id].success_rate = (
                self.models[model.model_id].success_rate * 0.7 + 
                recent_success_rate * 0.3
            )
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics and insights"""
        
        analytics = {
            "budget_tracking": self.budget_tracking.copy(),
            "model_performance": {},
            "routing_effectiveness": {},
            "cost_savings": {}
        }
        
        for model_id, history in self.performance_history.items():
            if history:
                success_rate = sum(1 for h in history if h["success"]) / len(history)
                avg_time = sum(h["generation_time"] for h in history if h["generation_time"]) / len([h for h in history if h["generation_time"]])
                
                analytics["model_performance"][model_id] = {
                    "total_attempts": len(history),
                    "success_rate": success_rate,
                    "avg_generation_time": avg_time,
                    "current_model_config": {
                        "cost": self.models[model_id].cost_per_generation,
                        "quality_score": self.models[model_id].quality_score
                    }
                }
        
        return analytics
    
    def save_state(self, filename: str = None):
        """Save orchestrator state for persistence"""
        
        if not filename:
            filename = f"orchestrator_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        state = {
            "performance_history": self.performance_history,
            "routing_decisions": self.routing_decisions,
            "budget_tracking": self.budget_tracking,
            "model_catalog": {
                model_id: {
                    "cost_per_generation": model.cost_per_generation,
                    "success_rate": model.success_rate,
                    "quality_score": model.quality_score,
                    "reliability_score": model.reliability_score
                }
                for model_id, model in self.models.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"💾 Orchestrator state saved: {filename}")
        return filename


async def demo_orchestrator():
    """Demonstrate the intelligent orchestrator"""
    
    print("🤖 INTELLIGENT MODEL ORCHESTRATOR DEMO")
    print("=" * 60)
    
    orchestrator = IntelligentModelOrchestrator()
    
    # Show cost optimization strategies
    strategies = orchestrator.get_cost_optimization_strategy()
    
    print("\n📊 COST OPTIMIZATION STRATEGIES:")
    for strategy_name, strategy in strategies["strategies"].items():
        print(f"\n🎯 {strategy_name.upper().replace('_', ' ')}:")
        print(f"   📝 {strategy['description']}")
        print(f"   💰 Estimated cost: ${strategy['estimated_cost']:.2f} for 2,639 posts")
        print(f"   📈 Cost per post: ${strategy['estimated_cost']/2639:.3f}")
    
    # Demo different request types
    test_requests = [
        GenerationRequest(
            content_type=ContentType.HERO_POST,
            budget_constraint=BudgetTier.HIGH,
            quality_requirement=9.0,
            features_required=["image-to-video"],
            priority=10
        ),
        GenerationRequest(
            content_type=ContentType.BULK_CONTENT,
            budget_constraint=BudgetTier.ULTRA_LOW,
            quality_requirement=5.0,
            features_required=["image-to-video"],
            priority=3
        ),
        GenerationRequest(
            content_type=ContentType.STANDARD_CONTENT,
            budget_constraint=BudgetTier.MEDIUM,
            quality_requirement=7.0,
            features_required=["image-to-video"],
            priority=6
        )
    ]
    
    print(f"\n🎬 INTELLIGENT ROUTING DEMO:")
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n--- Request {i}: {request.content_type.value} ---")
        
        primary_model, fallbacks = orchestrator.route_generation_request(request)
        
        print(f"🎯 Primary: {primary_model.model_id} (${primary_model.cost_per_generation:.3f})")
        print(f"🔄 Fallbacks: {[m.model_id for m in fallbacks]}")
        
        # Simulate execution
        result = await orchestrator.execute_generation_with_fallbacks(request)
        print(f"📊 Result: {'✅ Success' if result['success'] else '❌ Failed'}")
        if result["success"]:
            print(f"💰 Cost: ${result['cost']:.3f}, Model: {result['model_used']}")
    
    # Show analytics
    print(f"\n📈 PERFORMANCE ANALYTICS:")
    analytics = orchestrator.get_performance_analytics()
    
    print(f"💰 Budget tracking:")
    print(f"   Daily spend: ${analytics['budget_tracking']['daily_spend']:.3f}")
    print(f"   Monthly spend: ${analytics['budget_tracking']['monthly_spend']:.3f}")
    
    # Save state
    state_file = orchestrator.save_state()
    print(f"\n💾 State saved to: {state_file}")


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())