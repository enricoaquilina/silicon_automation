#!/usr/bin/env python3
"""
LangGraph Agentic System Launcher

Validates environment, installs dependencies, and runs the LangGraph
carousel extraction fixing system with Pydantic structured data.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path


def check_environment():
    """Check environment setup for LangGraph agent"""
    print("🔍 Checking LangGraph Agent Environment...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required for LangGraph")
        return False
    print(f"✅ Python version: {sys.version}")
    
    # Check for API keys (optional but recommended)
    api_keys = {
        "ANTHROPIC_API_KEY": "Anthropic Claude (recommended)",
        "OPENAI_API_KEY": "OpenAI GPT-4 (alternative)",
        "HUGGINGFACE_API_TOKEN": "Hugging Face (fallback)"
    }
    
    available_providers = []
    for key, description in api_keys.items():
        if os.getenv(key):
            available_providers.append(description)
            print(f"✅ {description} API key found")
        else:
            print(f"⚠️  {description} API key not set")
    
    if not available_providers:
        print("💡 No API keys found - will use local Hugging Face models")
        print("   For better performance, set one of:")
        for key, desc in api_keys.items():
            print(f"   export {key}='your_key_here'")
    
    # Check required files
    required_files = [
        "langgraph_carousel_agent.py",
        "production_browsermcp_extractor.py",
        "vlm_to_flux_local_fixed.py"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing required file: {file}")
            return False
        print(f"✅ Found: {file}")
    
    return True


def install_langgraph_dependencies():
    """Install LangGraph and related dependencies"""
    print("📦 Installing LangGraph dependencies...")
    
    try:
        # Install from requirements file
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "langgraph_requirements.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Dependency installation failed:")
            print(result.stderr)
            return False
        
        print("✅ LangGraph dependencies installed")
        
        # Test critical imports
        try:
            import langgraph
            import pydantic
            from langchain_core.messages import HumanMessage
            print("✅ Critical packages verified")
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("💡 Try installing manually: pip install langgraph pydantic langchain")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Installation timeout - please install manually")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False


def setup_workspace():
    """Set up workspace for LangGraph agent"""
    print("📁 Setting up LangGraph workspace...")
    
    workspace_dirs = [
        "langgraph_workspace",
        "langgraph_workspace/generated_fixes",
        "langgraph_workspace/tests",
        "langgraph_workspace/integration",
        "langgraph_workspace/reports"
    ]
    
    for dir_path in workspace_dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"   📂 Created: {dir_path}")
    
    return True


async def run_langgraph_agent():
    """Run the LangGraph agentic system"""
    print("\n🚀 Starting LangGraph Agentic System...")
    
    try:
        # Import the agent (after dependency check)
        from langgraph_carousel_agent import LangGraphCarouselAgent
        
        # Determine LLM provider based on available API keys
        if os.getenv("ANTHROPIC_API_KEY"):
            llm_provider = "anthropic"
            print("🧠 Using Anthropic Claude")
        elif os.getenv("OPENAI_API_KEY"):
            llm_provider = "openai"
            print("🧠 Using OpenAI GPT-4")
        else:
            llm_provider = "huggingface"
            print("🧠 Using Hugging Face local models")
        
        # Initialize the agent
        agent = LangGraphCarouselAgent(llm_provider=llm_provider)
        
        # Run the complete agentic workflow
        results = await agent.run_agentic_workflow()
        
        if "error" not in results:
            print("\n🎉 LangGraph Agentic System completed successfully!")
            print_results_summary(results)
        else:
            print(f"\n❌ Agentic system failed: {results['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LangGraph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_results_summary(results: dict):
    """Print a nice summary of the agent results"""
    print("\n📊 LANGGRAPH AGENTIC SYSTEM RESULTS")
    print("=" * 60)
    print(f"🎯 Success Rate: {results.get('success_rate', 0):.1%}")
    print(f"🔧 Fixes Generated: {results.get('fixes_generated', 0)}")
    print(f"🧪 Tests Created: {results.get('tests_created', 0)}")
    print(f"📋 Issues Addressed: {results.get('issues_identified', 0)}")
    print(f"🔗 Integration Status: {results.get('integration_status', {})}")
    
    print(f"\n📁 Output Locations:")
    print(f"   🔧 Generated Fixes: langgraph_workspace/fix_*.py")
    print(f"   🧪 Test Suites: langgraph_workspace/test_*.py")
    print(f"   🔗 Unified Pipeline: langgraph_workspace/unified_extraction_generation_pipeline.py")
    print(f"   🚀 Deployment Script: langgraph_workspace/deploy_fixed_pipeline.py")
    print(f"   📄 Detailed Reports: langgraph_workspace/langgraph_report_*.json")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Review generated fixes in langgraph_workspace/")
    print(f"   2. Run deployment script to apply fixes")
    print(f"   3. Execute test suites to validate fixes")
    print(f"   4. Deploy unified pipeline for production use")


def show_usage_examples():
    """Show usage examples and tips"""
    print("\n💡 USAGE EXAMPLES")
    print("=" * 30)
    print("# Basic usage with Anthropic Claude:")
    print("export ANTHROPIC_API_KEY='your_key_here'")
    print("python run_langgraph_agent.py")
    print()
    print("# Using OpenAI instead:")
    print("export OPENAI_API_KEY='your_key_here'")
    print("python run_langgraph_agent.py")
    print()
    print("# Local-only mode (no API keys needed):")
    print("python run_langgraph_agent.py")
    print()
    print("🎯 Features:")
    print("   • Structured Pydantic data models")
    print("   • Multi-agent workflow orchestration")
    print("   • Automatic code generation and testing")
    print("   • VLM pipeline integration")
    print("   • Comprehensive error handling")
    print("   • State checkpointing and recovery")


def main():
    """Main launcher function"""
    print("🤖 LangGraph Agentic Carousel Fixer")
    print("=" * 50)
    
    # Step 1: Environment check
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        show_usage_examples()
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_langgraph_dependencies():
        print("\n❌ Dependency installation failed.")
        print("💡 Try manually: pip install -r langgraph_requirements.txt")
        sys.exit(1)
    
    # Step 3: Setup workspace
    if not setup_workspace():
        print("\n❌ Workspace setup failed.")
        sys.exit(1)
    
    # Step 4: Run the agentic system
    print("\n✅ All checks passed. Starting LangGraph agent...")
    success = asyncio.run(run_langgraph_agent())
    
    if success:
        print("\n🎉 LangGraph Agentic System execution completed!")
        print("\n🔗 Integration with VLM pipeline ready for production deployment")
    else:
        print("\n❌ LangGraph execution failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()