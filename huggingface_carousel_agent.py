#!/usr/bin/env python3
"""
Hugging Face Carousel Agent

Uses top-performing code generation models from Hugging Face
to fix carousel extraction issues without Replicate dependency
"""

import asyncio
import json
import os
import sys
import subprocess
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Try to import optional dependencies
try:
    import accelerate
    has_accelerate = True
except ImportError:
    has_accelerate = False


class HuggingFaceCodeAgent:
    """AI-powered agent using Hugging Face models for fixing Instagram carousel extraction"""
    
    def __init__(self, work_dir: str = None, model_name: str = None):
        self.work_dir = Path(work_dir or "/Users/enricoaquilina/Documents/Fraud/silicon_automation")
        self.model_name = model_name or self._get_best_code_model()
        
        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        self.workspace = self.work_dir / "agent_workspace"
        self.workspace.mkdir(exist_ok=True)
        
        print(f"🤖 Hugging Face Carousel Agent initialized")
        print(f"   📁 Work directory: {self.work_dir}")
        print(f"   🔧 Using model: {self.model_name}")
        print(f"   💾 Workspace: {self.workspace}")
    
    def _get_best_code_model(self) -> str:
        """Select the best available code generation model"""
        # List of high-performance code models (in order of preference)
        models = [
            "microsoft/DialoGPT-medium",  # Fast, good for conversations
            "microsoft/CodeGPT-small-py", # Python-specific
            "Salesforce/codegen-350M-mono", # Code generation specialist
            "bigcode/starcoder",  # If available
            "WizardLM/WizardCoder-15B-V1.0"  # High performance
        ]
        
        # Return first available model (can be enhanced with actual availability checking)
        return models[0]  # Start with smallest reliable model
    
    def initialize_model(self):
        """Initialize the Hugging Face model"""
        try:
            print(f"🔄 Loading model: {self.model_name}")
            
            # Use pipeline for easier handling
            device = 0 if torch.cuda.is_available() else -1
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device=device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )
            
            print(f"✅ Model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            print("💡 Falling back to API-based approach...")
            return False
    
    def generate_code_with_huggingface(self, task_description: str, context: Dict[str, Any]) -> Tuple[str, Any]:
        """Generate code using Hugging Face model or API"""
        
        # Create detailed prompt for code generation
        prompt = f"""
# Task: {task_description}

# Context:
{json.dumps(context, indent=2)}

# Requirements:
- Fix Instagram carousel navigation issues
- Use BrowserMCP tools and async/await patterns
- Include comprehensive error handling
- Add logging for debugging
- Follow Python best practices

# Generate Python code:
```python
"""

        try:
            if self.pipeline:
                # Use local model
                response = self.pipeline(
                    prompt,
                    max_length=2048,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.pipeline.tokenizer.eos_token_id
                )
                
                generated_text = response[0]['generated_text']
                code_start = generated_text.find('```python')
                if code_start != -1:
                    code_end = generated_text.find('```', code_start + 9)
                    if code_end != -1:
                        code = generated_text[code_start + 9:code_end].strip()
                        return generated_text, code
                
                return generated_text, None
            else:
                # Fallback to Hugging Face API
                return self._use_huggingface_api(prompt)
                
        except Exception as e:
            return f"Code generation error: {str(e)}", None
    
    def _use_huggingface_api(self, prompt: str) -> Tuple[str, Any]:
        """Use Hugging Face Inference API as fallback"""
        try:
            api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN', '')}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 2048,
                    "temperature": 0.1,
                    "return_full_text": False
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result[0]['generated_text'] if isinstance(result, list) else result['generated_text']
                return generated_text, generated_text
            else:
                return f"API Error: {response.status_code} - {response.text}", None
                
        except Exception as e:
            return f"API error: {str(e)}", None
    
    async def fix_carousel_navigation_with_ai(self) -> Dict[str, Any]:
        """Use AI to fix carousel navigation issues"""
        print("\n🔧 Using AI to fix carousel navigation...")
        
        context = {
            "issue": "carousel_nav_001 - Button detection failures",
            "current_file": "production_browsermcp_extractor.py",
            "problem": "Instagram UI changes break CSS selectors for navigation buttons",
            "solution_approach": "Multi-strategy navigation with fallbacks"
        }
        
        task_description = """
        Fix Instagram carousel navigation by implementing a robust multi-strategy approach.
        The current single-selector method fails when Instagram changes their UI.
        
        Create a method called 'robust_carousel_navigation' that tries multiple strategies:
        1. Multiple CSS selectors for next/previous buttons
        2. Keyboard navigation (arrow keys)
        3. Touch/swipe simulation
        4. JavaScript injection as last resort
        
        Include proper error handling and waiting between attempts.
        """
        
        generated_code, extracted_code = self.generate_code_with_huggingface(task_description, context)
        
        if extracted_code:
            # Save the generated fix
            fix_file = self.workspace / "ai_generated_navigation_fix.py"
            fix_file.write_text(extracted_code)
            print(f"✅ AI-generated navigation fix saved: {fix_file}")
        
        return {
            "success": extracted_code is not None,
            "generated_code": generated_code,
            "extracted_code": extracted_code,
            "context": context
        }
    
    async def fix_timing_issues_with_ai(self) -> Dict[str, Any]:
        """Use AI to fix timing and async loading issues"""
        print("\n⏱️  Using AI to fix timing issues...")
        
        context = {
            "issue": "carousel_nav_002 - Async loading delays",
            "problem": "Images load after navigation attempts, causing failures",
            "solution_approach": "Intelligent waiting with content stability detection"
        }
        
        task_description = """
        Fix Instagram carousel timing issues by implementing intelligent waiting.
        The current method doesn't wait for dynamic content to fully load.
        
        Create methods for:
        1. 'intelligent_wait_for_content' - Wait for images to actually load
        2. 'wait_for_navigation_complete' - Detect when carousel navigation finishes
        3. Proper content stability detection
        
        Use async/await patterns and include timeout handling.
        """
        
        generated_code, extracted_code = self.generate_code_with_huggingface(task_description, context)
        
        if extracted_code:
            fix_file = self.workspace / "ai_generated_timing_fix.py"
            fix_file.write_text(extracted_code)
            print(f"✅ AI-generated timing fix saved: {fix_file}")
        
        return {
            "success": extracted_code is not None,
            "generated_code": generated_code,
            "extracted_code": extracted_code,
            "context": context
        }
    
    async def create_comprehensive_tests_with_ai(self) -> Dict[str, Any]:
        """Use AI to create comprehensive test suite"""
        print("\n🧪 Using AI to create test suite...")
        
        context = {
            "test_framework": "pytest",
            "test_shortcodes": ["C0xFHGOrBN7", "C0wmEEKItfR", "C0xMpxwKoxb"],
            "components_to_test": ["navigation", "timing", "popup_handling", "extraction_accuracy"]
        }
        
        task_description = """
        Create a comprehensive pytest test suite for the fixed carousel extractor.
        
        Include tests for:
        1. Navigation reliability with different strategies
        2. Timing and content loading
        3. Popup handling
        4. Extraction accuracy
        5. Integration tests
        6. End-to-end workflow tests
        
        Use async test patterns and proper fixtures.
        """
        
        generated_code, extracted_code = self.generate_code_with_huggingface(task_description, context)
        
        if extracted_code:
            test_file = self.workspace / "ai_generated_comprehensive_tests.py"
            test_file.write_text(extracted_code)
            print(f"✅ AI-generated test suite saved: {test_file}")
        
        return {
            "success": extracted_code is not None,
            "generated_code": generated_code,
            "extracted_code": extracted_code,
            "context": context
        }
    
    async def create_vlm_integration_with_ai(self) -> Dict[str, Any]:
        """Use AI to create VLM pipeline integration"""
        print("\n🔗 Using AI to create VLM integration...")
        
        context = {
            "existing_vlm_file": "vlm_to_flux_local_fixed.py",
            "existing_extractor": "production_browsermcp_extractor.py",
            "integration_goal": "Combined extraction + generation workflow"
        }
        
        task_description = """
        Create a unified pipeline that combines the fixed carousel extractor with the VLM-to-Flux pipeline.
        
        The pipeline should:
        1. Extract images from Instagram using the fixed extractor
        2. Pass extracted images to VLM analysis
        3. Generate SiliconSentiments branded content using Flux
        4. Save results to both GridFS and local filesystem
        5. Provide comprehensive reporting
        
        Include proper error handling and batch processing capabilities.
        """
        
        generated_code, extracted_code = self.generate_code_with_huggingface(task_description, context)
        
        if extracted_code:
            integration_file = self.workspace / "ai_generated_unified_pipeline.py"
            integration_file.write_text(extracted_code)
            print(f"✅ AI-generated integration saved: {integration_file}")
        
        return {
            "success": extracted_code is not None,
            "generated_code": generated_code,
            "extracted_code": extracted_code,
            "context": context
        }
    
    async def run_complete_ai_workflow(self):
        """Run the complete AI-powered fixing workflow"""
        print("\n🚀 Starting Hugging Face AI Workflow")
        print("=" * 60)
        
        # Initialize model
        model_loaded = self.initialize_model()
        if not model_loaded:
            print("⚠️  Using API fallback mode")
        
        # Execute AI-powered fixes
        tasks = [
            ("navigation", self.fix_carousel_navigation_with_ai),
            ("timing", self.fix_timing_issues_with_ai),
            ("tests", self.create_comprehensive_tests_with_ai),
            ("integration", self.create_vlm_integration_with_ai)
        ]
        
        results = {}
        
        for task_name, task_func in tasks:
            try:
                print(f"\n🔄 Running {task_name} AI task...")
                result = await task_func()
                results[task_name] = result
                
                if result["success"]:
                    print(f"✅ {task_name} completed successfully")
                else:
                    print(f"⚠️  {task_name} had issues but continued")
                    
            except Exception as e:
                print(f"❌ {task_name} failed: {str(e)}")
                results[task_name] = {"success": False, "error": str(e)}
        
        # Generate summary report
        self._generate_ai_workflow_report(results)
        
        return results
    
    def _generate_ai_workflow_report(self, results: Dict[str, Any]):
        """Generate comprehensive AI workflow report"""
        print("\n📊 AI WORKFLOW SUMMARY")
        print("=" * 60)
        
        total_tasks = len(results)
        successful_tasks = len([r for r in results.values() if r.get("success", False)])
        
        print(f"📈 Success Rate: {successful_tasks}/{total_tasks} ({successful_tasks/total_tasks*100:.1f}%)")
        print(f"🤖 Model Used: {self.model_name}")
        
        print(f"\n✅ Generated Components:")
        for task_name, result in results.items():
            if result.get("success"):
                print(f"   🔧 {task_name} - AI-generated solution ready")
            else:
                print(f"   ❌ {task_name} - Failed or incomplete")
        
        print(f"\n📁 All outputs saved in: {self.workspace}")
        
        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_name,
            "success_rate": f"{successful_tasks/total_tasks*100:.1f}%",
            "detailed_results": results
        }
        
        report_file = self.workspace / f"ai_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        print(f"📄 Detailed report: {report_file}")


async def main():
    """Main execution function"""
    
    # Check for optional Hugging Face token
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not hf_token:
        print("💡 Tip: Set HUGGINGFACE_API_TOKEN for API fallback mode")
    
    # Initialize and run AI agent
    agent = HuggingFaceCodeAgent()
    results = await agent.run_complete_ai_workflow()
    
    print(f"\n🎉 Hugging Face AI Workflow completed!")
    
    # Show next steps
    successful_tasks = len([r for r in results.values() if r.get("success", False)])
    if successful_tasks > 0:
        print(f"\n🚀 Next Steps:")
        print(f"   1. Review AI-generated code in agent_workspace/")
        print(f"   2. Apply fixes to production_browsermcp_extractor.py")
        print(f"   3. Run tests and validate improvements")
        print(f"   4. Test unified extraction + VLM pipeline")


if __name__ == "__main__":
    asyncio.run(main())