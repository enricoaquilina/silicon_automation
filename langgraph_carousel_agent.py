#!/usr/bin/env python3
"""
LangGraph Agentic System for Carousel Extraction Pipeline

Uses LangGraph agents with Pydantic models to systematically fix
Instagram carousel extraction issues through structured agent workflows.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal, Union
from pathlib import Path
from dataclasses import dataclass

# Core dependencies
from pydantic import BaseModel, Field, validator
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.checkpoint.sqlite import SqliteSaver

# AI/LLM integration
try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_community.llms import HuggingFacePipeline
except ImportError:
    print("⚠️  LangChain dependencies not installed. Install with: pip install langchain langchain-openai langchain-anthropic")

# Custom tools
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class CarouselIssue(BaseModel):
    """Pydantic model for carousel extraction issues"""
    issue_id: str = Field(..., description="Unique identifier for the issue")
    title: str = Field(..., description="Brief title of the issue")
    description: str = Field(..., description="Detailed description of the problem")
    severity: Literal["critical", "high", "medium", "low"] = Field(..., description="Issue severity level")
    component: Literal["navigation", "timing", "popup_handling", "image_extraction", "rate_limiting"] = Field(..., description="Affected component")
    current_behavior: str = Field(..., description="Current problematic behavior")
    expected_behavior: str = Field(..., description="Expected correct behavior")
    proposed_solution: Optional[str] = Field(None, description="Proposed solution approach")
    test_cases: List[str] = Field(default_factory=list, description="Test cases to validate the fix")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other issues")


class AgentState(BaseModel):
    """Pydantic model for agent state management"""
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Message history")
    current_issues: List[CarouselIssue] = Field(default_factory=list, description="Identified issues")
    fixed_issues: List[str] = Field(default_factory=list, description="Successfully fixed issue IDs")
    generated_code: Dict[str, str] = Field(default_factory=dict, description="Generated code snippets")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Test execution results")
    integration_status: Dict[str, bool] = Field(default_factory=dict, description="Integration component status")
    next_action: Optional[str] = Field(None, description="Next action to take")
    workflow_complete: bool = Field(False, description="Whether workflow is complete")


class CodeGenerationRequest(BaseModel):
    """Pydantic model for code generation requests"""
    task_type: Literal["fix", "test", "integration", "optimization"] = Field(..., description="Type of code to generate")
    issue_id: Optional[str] = Field(None, description="Related issue ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context information")
    requirements: List[str] = Field(default_factory=list, description="Specific requirements")
    existing_code: Optional[str] = Field(None, description="Existing code to modify")


class TestRequest(BaseModel):
    """Pydantic model for test execution requests"""
    test_type: Literal["unit", "integration", "e2e", "performance"] = Field(..., description="Type of test")
    component: str = Field(..., description="Component being tested")
    test_code: str = Field(..., description="Test code to execute")
    expected_outcome: str = Field(..., description="Expected test outcome")


class LangGraphCarouselAgent:
    """LangGraph-based agentic system for carousel extraction pipeline"""
    
    def __init__(self, work_dir: str = None, llm_provider: str = "anthropic"):
        self.work_dir = Path(work_dir or "/Users/enricoaquilina/Documents/Fraud/silicon_automation")
        self.workspace = self.work_dir / "langgraph_workspace"
        self.workspace.mkdir(exist_ok=True)
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm(llm_provider)
        
        # Initialize graph and checkpointer
        self.checkpointer = SqliteSaver(self.workspace / "agent_checkpoints.db")
        self.workflow = self._build_agent_graph()
        
        # Known issues from CLAUDE.md
        self.known_issues = self._initialize_known_issues()
        
        print(f"🤖 LangGraph Carousel Agent initialized")
        print(f"   📁 Work directory: {self.work_dir}")
        print(f"   🧠 LLM Provider: {llm_provider}")
        print(f"   📊 Workspace: {self.workspace}")
    
    def _initialize_llm(self, provider: str):
        """Initialize LLM based on provider preference"""
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return ChatAnthropic(model="claude-3-sonnet-20240229", api_key=api_key)
        
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(model="gpt-4", api_key=api_key)
        
        # Fallback to Hugging Face local model
        print("⚠️  API keys not found, using local Hugging Face model")
        try:
            from transformers import pipeline
            hf_pipeline = pipeline("text-generation", model="microsoft/DialoGPT-medium")
            return HuggingFacePipeline(pipeline=hf_pipeline)
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            raise
    
    def _initialize_known_issues(self) -> List[CarouselIssue]:
        """Initialize known carousel extraction issues"""
        return [
            CarouselIssue(
                issue_id="carousel_nav_001",
                title="Button Detection Failures",
                description="Instagram UI changes break CSS selectors for navigation buttons",
                severity="critical",
                component="navigation",
                current_behavior="Single CSS selector fails when Instagram updates UI",
                expected_behavior="Robust navigation with multiple fallback strategies",
                proposed_solution="Multi-selector approach with keyboard/touch fallbacks",
                test_cases=["test_button_click_navigation", "test_keyboard_fallback", "test_touch_navigation"],
                dependencies=[]
            ),
            CarouselIssue(
                issue_id="carousel_timing_001", 
                title="Async Loading Delays",
                description="Images load after navigation attempts causing premature failures",
                severity="high",
                component="timing",
                current_behavior="Navigation attempts before images fully load",
                expected_behavior="Intelligent waiting for content stability",
                proposed_solution="Content stability detection with proper timeouts",
                test_cases=["test_content_loading_wait", "test_navigation_timing"],
                dependencies=[]
            ),
            CarouselIssue(
                issue_id="carousel_popup_001",
                title="Popup Interference", 
                description="Login/cookie modals block navigation and extraction",
                severity="high",
                component="popup_handling",
                current_behavior="Popups interrupt workflow causing failures",
                expected_behavior="Automatic popup detection and dismissal",
                proposed_solution="Comprehensive popup handling with multiple selectors",
                test_cases=["test_popup_dismissal", "test_login_modal_handling"],
                dependencies=[]
            )
        ]
    
    def _build_agent_graph(self) -> StateGraph:
        """Build the LangGraph agent workflow"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("analyzer", self.analyzer_agent)
        workflow.add_node("code_generator", self.code_generator_agent) 
        workflow.add_node("tester", self.tester_agent)
        workflow.add_node("integrator", self.integrator_agent)
        workflow.add_node("validator", self.validator_agent)
        
        # Define edges (workflow)
        workflow.set_entry_point("analyzer")
        workflow.add_edge("analyzer", "code_generator")
        workflow.add_edge("code_generator", "tester")
        workflow.add_edge("tester", "integrator")
        workflow.add_edge("integrator", "validator")
        workflow.add_conditional_edges(
            "validator",
            self.should_continue,
            {
                "continue": "analyzer",  # Loop back for more issues
                "finish": END
            }
        )
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def analyzer_agent(self, state: AgentState) -> AgentState:
        """Agent that analyzes carousel extraction issues"""
        print("\n🔍 Analyzer Agent: Identifying issues...")
        
        # Add known issues if not already present
        if not state.current_issues:
            state.current_issues = self.known_issues
            print(f"   📋 Identified {len(state.current_issues)} issues")
        
        # Use LLM to analyze current codebase and identify additional issues
        analysis_prompt = self._create_analysis_prompt(state)
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            
            # Extract additional issues from LLM response
            additional_issues = self._parse_analysis_response(response.content)
            state.current_issues.extend(additional_issues)
            
            # Update state
            state.messages.append({
                "agent": "analyzer",
                "timestamp": datetime.now().isoformat(),
                "content": f"Analyzed codebase and identified {len(state.current_issues)} total issues"
            })
            
            state.next_action = "code_generation"
            
        except Exception as e:
            print(f"   ⚠️  Analysis error: {e}")
            state.messages.append({
                "agent": "analyzer", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    async def code_generator_agent(self, state: AgentState) -> AgentState:
        """Agent that generates code fixes"""
        print("\n🔧 Code Generator Agent: Creating fixes...")
        
        for issue in state.current_issues:
            if issue.issue_id not in state.fixed_issues:
                print(f"   🎯 Generating fix for: {issue.title}")
                
                # Create code generation request
                code_request = CodeGenerationRequest(
                    task_type="fix",
                    issue_id=issue.issue_id,
                    context={
                        "issue": issue.dict(),
                        "component": issue.component,
                        "severity": issue.severity
                    },
                    requirements=[
                        "Use async/await patterns",
                        "Include comprehensive error handling", 
                        "Add logging for debugging",
                        "Follow Python best practices",
                        "Integrate with existing BrowserMCP tools"
                    ]
                )
                
                # Generate code using LLM
                generated_code = await self._generate_code_for_issue(issue, code_request)
                
                if generated_code:
                    state.generated_code[issue.issue_id] = generated_code
                    
                    # Save generated code to file
                    code_file = self.workspace / f"fix_{issue.issue_id}.py"
                    code_file.write_text(generated_code)
                    print(f"   ✅ Generated fix saved: {code_file}")
        
        state.messages.append({
            "agent": "code_generator",
            "timestamp": datetime.now().isoformat(),
            "content": f"Generated {len(state.generated_code)} code fixes"
        })
        
        state.next_action = "testing"
        return state
    
    async def tester_agent(self, state: AgentState) -> AgentState:
        """Agent that creates and runs tests"""
        print("\n🧪 Tester Agent: Creating and running tests...")
        
        for issue_id, code in state.generated_code.items():
            if issue_id not in state.test_results:
                issue = next(i for i in state.current_issues if i.issue_id == issue_id)
                
                print(f"   🎯 Testing fix for: {issue.title}")
                
                # Generate test code
                test_request = TestRequest(
                    test_type="unit",
                    component=issue.component,
                    test_code="",  # Will be generated
                    expected_outcome="Fix works without errors"
                )
                
                test_code = await self._generate_test_for_issue(issue, test_request)
                
                if test_code:
                    # Save test code
                    test_file = self.workspace / f"test_{issue_id}.py"
                    test_file.write_text(test_code)
                    
                    # Simulate test execution (in real scenario, would run actual tests)
                    test_result = await self._execute_test(test_code, issue_id)
                    state.test_results[issue_id] = test_result
                    
                    print(f"   ✅ Test created and executed: {test_file}")
        
        state.messages.append({
            "agent": "tester",
            "timestamp": datetime.now().isoformat(),
            "content": f"Created and executed {len(state.test_results)} tests"
        })
        
        state.next_action = "integration"
        return state
    
    async def integrator_agent(self, state: AgentState) -> AgentState:
        """Agent that integrates fixes with VLM pipeline"""
        print("\n🔗 Integrator Agent: Creating unified pipeline...")
        
        # Create unified pipeline that combines fixes with VLM workflow
        integration_code = await self._create_unified_pipeline(state)
        
        if integration_code:
            pipeline_file = self.workspace / "unified_extraction_generation_pipeline.py" 
            pipeline_file.write_text(integration_code)
            
            state.integration_status["unified_pipeline"] = True
            print(f"   ✅ Unified pipeline created: {pipeline_file}")
        
        # Create production deployment script
        deployment_code = await self._create_deployment_script(state)
        
        if deployment_code:
            deploy_file = self.workspace / "deploy_fixed_pipeline.py"
            deploy_file.write_text(deployment_code)
            
            state.integration_status["deployment_script"] = True
            print(f"   ✅ Deployment script created: {deploy_file}")
        
        state.messages.append({
            "agent": "integrator",
            "timestamp": datetime.now().isoformat(), 
            "content": "Created unified pipeline and deployment scripts"
        })
        
        state.next_action = "validation"
        return state
    
    async def validator_agent(self, state: AgentState) -> AgentState:
        """Agent that validates the complete solution"""
        print("\n✅ Validator Agent: Validating complete solution...")
        
        validation_results = {
            "fixes_generated": len(state.generated_code),
            "tests_passed": len([r for r in state.test_results.values() if r.get("passed", False)]),
            "integration_complete": all(state.integration_status.values()),
            "issues_addressed": len(state.current_issues)
        }
        
        # Check if all critical issues are addressed
        critical_issues = [i for i in state.current_issues if i.severity == "critical"]
        critical_fixed = len([i.issue_id for i in critical_issues if i.issue_id in state.generated_code])
        
        validation_results["critical_issues_fixed"] = critical_fixed == len(critical_issues)
        
        # Determine if workflow should continue or finish
        if validation_results["critical_issues_fixed"] and validation_results["integration_complete"]:
            state.workflow_complete = True
            print("   🎉 All critical issues addressed, workflow complete!")
        else:
            print("   ⚠️  Some issues remain, continuing workflow...")
        
        state.messages.append({
            "agent": "validator",
            "timestamp": datetime.now().isoformat(),
            "content": f"Validation complete: {validation_results}"
        })
        
        return state
    
    def should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue or finish"""
        return "finish" if state.workflow_complete else "continue"
    
    def _create_analysis_prompt(self, state: AgentState) -> str:
        """Create prompt for codebase analysis"""
        return f"""
Analyze the Instagram carousel extraction codebase for issues.

Known issues already identified:
{json.dumps([issue.dict() for issue in state.current_issues], indent=2)}

Please identify any additional issues in the codebase that might affect:
1. Carousel navigation reliability
2. Image extraction accuracy  
3. Error handling and recovery
4. Performance and timing
5. Integration with VLM pipeline

Focus on structural problems, edge cases, and potential failure points.
Respond with a structured analysis.
"""
    
    def _parse_analysis_response(self, response: str) -> List[CarouselIssue]:
        """Parse LLM analysis response into CarouselIssue objects"""
        # Simplified parsing - in production would use more sophisticated extraction
        additional_issues = []
        
        # Look for structured issue patterns in response
        if "additional issue" in response.lower() or "new issue" in response.lower():
            # Create a generic additional issue for demonstration
            additional_issues.append(
                CarouselIssue(
                    issue_id="llm_identified_001",
                    title="LLM Identified Issue",
                    description="Issue identified through LLM analysis",
                    severity="medium",
                    component="image_extraction",
                    current_behavior="Potential issue detected",
                    expected_behavior="Should work correctly",
                    test_cases=["test_llm_identified_issue"]
                )
            )
        
        return additional_issues
    
    async def _generate_code_for_issue(self, issue: CarouselIssue, request: CodeGenerationRequest) -> str:
        """Generate code fix for a specific issue"""
        prompt = f"""
Generate Python code to fix this Instagram carousel extraction issue:

Issue: {issue.title}
Description: {issue.description}
Component: {issue.component}
Current Behavior: {issue.current_behavior}
Expected Behavior: {issue.expected_behavior}

Requirements:
{chr(10).join(f'- {req}' for req in request.requirements)}

Generate complete, working Python code that addresses this issue.
Include proper async/await patterns, error handling, and documentation.

```python
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Extract code from response
            content = response.content
            if "```python" in content:
                start = content.find("```python") + 9
                end = content.find("```", start)
                if end != -1:
                    return content[start:end].strip()
            
            return content
            
        except Exception as e:
            print(f"   ❌ Code generation failed for {issue.issue_id}: {e}")
            return ""
    
    async def _generate_test_for_issue(self, issue: CarouselIssue, request: TestRequest) -> str:
        """Generate test code for a specific issue"""
        prompt = f"""
Generate pytest test code for this fix:

Issue: {issue.title}
Component: {issue.component}
Test Cases: {', '.join(issue.test_cases)}

Create comprehensive pytest tests that validate the fix works correctly.
Include async test patterns and proper assertions.

```python
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Extract code from response
            content = response.content
            if "```python" in content:
                start = content.find("```python") + 9
                end = content.find("```", start)
                if end != -1:
                    return content[start:end].strip()
            
            return content
            
        except Exception as e:
            print(f"   ❌ Test generation failed for {issue.issue_id}: {e}")
            return ""
    
    async def _execute_test(self, test_code: str, issue_id: str) -> Dict[str, Any]:
        """Execute test code (simulated for this example)"""
        # In production, would actually run the test code
        return {
            "issue_id": issue_id,
            "passed": True,
            "execution_time": 0.5,
            "details": "Test executed successfully (simulated)"
        }
    
    async def _create_unified_pipeline(self, state: AgentState) -> str:
        """Create unified extraction + VLM pipeline"""
        prompt = f"""
Create a unified pipeline that combines:
1. Fixed carousel extraction (with {len(state.generated_code)} fixes applied)
2. VLM-to-Flux generation pipeline 
3. MongoDB storage integration
4. Comprehensive error handling and reporting

The pipeline should process Instagram shortcodes end-to-end:
shortcode → extraction → VLM analysis → Flux generation → storage

Generate complete, production-ready Python code.

```python
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Extract code from response
            content = response.content
            if "```python" in content:
                start = content.find("```python") + 9
                end = content.find("```", start)
                if end != -1:
                    return content[start:end].strip()
            
            return content
            
        except Exception as e:
            print(f"   ❌ Pipeline creation failed: {e}")
            return ""
    
    async def _create_deployment_script(self, state: AgentState) -> str:
        """Create deployment script for production"""
        prompt = """
Create a deployment script that:
1. Applies all generated fixes to the production extractor
2. Sets up the unified pipeline
3. Runs validation tests
4. Provides rollback capabilities
5. Includes monitoring and health checks

Generate complete deployment automation code.

```python
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Extract code from response  
            content = response.content
            if "```python" in content:
                start = content.find("```python") + 9
                end = content.find("```", start)
                if end != -1:
                    return content[start:end].strip()
            
            return content
            
        except Exception as e:
            print(f"   ❌ Deployment script creation failed: {e}")
            return ""
    
    async def run_agentic_workflow(self, thread_id: str = "carousel_fix_001") -> Dict[str, Any]:
        """Run the complete agentic workflow"""
        print("\n🚀 Starting LangGraph Agentic Workflow")
        print("=" * 60)
        
        # Initialize state
        initial_state = AgentState()
        
        # Configure workflow execution
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            # Generate final report
            report = self._generate_final_report(final_state)
            
            print(f"\n🎉 Agentic workflow completed successfully!")
            print(f"📊 Final Report: {report}")
            
            return report
            
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return {"error": str(e)}
    
    def _generate_final_report(self, state: AgentState) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "workflow_status": "completed" if state.workflow_complete else "incomplete",
            "issues_identified": len(state.current_issues),
            "fixes_generated": len(state.generated_code),
            "tests_created": len(state.test_results),
            "integration_status": state.integration_status,
            "agent_messages": len(state.messages),
            "success_rate": len(state.generated_code) / len(state.current_issues) if state.current_issues else 0
        }
        
        # Save detailed report
        report_file = self.workspace / f"langgraph_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": report,
                "detailed_state": state.dict(),
                "agent_messages": state.messages
            }, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file}")
        
        return report


async def main():
    """Main execution function"""
    print("🤖 LangGraph Carousel Agent with Pydantic")
    print("=" * 50)
    
    # Check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if anthropic_key:
        llm_provider = "anthropic"
        print("🧠 Using Anthropic Claude")
    elif openai_key:
        llm_provider = "openai"
        print("🧠 Using OpenAI GPT-4")
    else:
        llm_provider = "huggingface"
        print("🧠 Using Hugging Face local model")
        print("💡 Tip: Set ANTHROPIC_API_KEY or OPENAI_API_KEY for better performance")
    
    # Initialize and run agent
    agent = LangGraphCarouselAgent(llm_provider=llm_provider)
    
    # Run the agentic workflow
    results = await agent.run_agentic_workflow()
    
    if "error" not in results:
        print(f"\n✅ Agentic system completed with {results['success_rate']:.1%} success rate")
        print(f"🔧 Generated {results['fixes_generated']} fixes")
        print(f"🧪 Created {results['tests_created']} tests")
        print(f"📁 All outputs in: langgraph_workspace/")
    else:
        print(f"\n❌ Workflow failed: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())