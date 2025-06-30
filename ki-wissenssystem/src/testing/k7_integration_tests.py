"""
K7 INTEGRATION TESTS - LITELLM REQUEST VALIDATION
=================================================

Spezifische Tests für die K7 Enterprise Validation:
- Direct LiteLLM Client Testing
- Request Inspector Integration
- Smart Alias Model Resolution
- Mock Response Validation

Diese Tests validieren die Korrektheit der internen Logik
ohne externe API-Abhängigkeiten.
"""

import asyncio
import json
import pytest
import time
from typing import Dict, Any, List
import logging

from litellm_request_inspector import (
    LLMRequestInspector,
    CapturedRequest,
    create_test_session
)
from enterprise_test_orchestrator import (
    EnterpriseTestOrchestrator,
    create_enterprise_orchestrator
)

logger = logging.getLogger(__name__)

class TestK7LiteLLMIntegration:
    """Direct K7 LiteLLM Integration Tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_session(self):
        """Setup clean test session for each test"""
        self.inspector = create_test_session("k7_integration_test")
        self.inspector.clear_session()
        
        yield
        
        # Cleanup
        self.inspector.clear_session()
    
    def test_request_inspector_basic_functionality(self):
        """Test basic request capture and mock response generation"""
        
        # Test request
        test_request = {
            "model": "classification_premium",
            "messages": [
                {"role": "system", "content": "Klassifiziere das folgende Dokument"},
                {"role": "user", "content": "Das ist ein BSI C5 Compliance-Dokument"}
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
            "task_type": "CLASSIFICATION",
            "tier": "PREMIUM",
            "priority": 1
        }
        
        # Capture request
        mock_response = self.inspector.capture_request_callback(test_request)
        
        # Validate mock response structure
        assert "choices" in mock_response
        assert "usage" in mock_response
        assert len(mock_response["choices"]) > 0
        assert "message" in mock_response["choices"][0]
        assert "content" in mock_response["choices"][0]["message"]
        
        # Validate request was captured
        captured_requests = self.inspector.get_captured_requests()
        assert len(captured_requests) == 1
        
        captured = captured_requests[0]
        assert captured.model == "classification_premium"
        assert captured.task_type == "CLASSIFICATION"
        assert captured.tier == "PREMIUM"
        assert captured.priority == 1
        assert captured.temperature == 0.1
    
    def test_smart_alias_model_resolution(self):
        """Test all Smart Alias models resolve correctly"""
        
        smart_aliases = [
            ("classification_premium", "PREMIUM", 1),
            ("classification_balanced", "BALANCED", 2),
            ("classification_cost_effective", "COST_EFFECTIVE", 3),
            ("extraction_premium", "PREMIUM", 2),
            ("extraction_balanced", "BALANCED", 2),
            ("extraction_cost_effective", "COST_EFFECTIVE", 3),
            ("synthesis_premium", "PREMIUM", 4),
            ("synthesis_balanced", "BALANCED", 4),
            ("synthesis_cost_effective", "COST_EFFECTIVE", 4),
            ("validation_primary_premium", "PREMIUM", 1),
            ("validation_secondary_premium", "PREMIUM", 1)
        ]
        
        resolution_results = []
        
        for alias, expected_tier, expected_priority in smart_aliases:
            test_request = {
                "model": alias,
                "messages": [{"role": "user", "content": f"Test {alias}"}],
                "temperature": 0.1,
                "tier": expected_tier,
                "priority": expected_priority
            }
            
            start_time = time.time()
            mock_response = self.inspector.capture_request_callback(test_request)
            resolution_time = time.time() - start_time
            
            # Validate response
            assert "choices" in mock_response
            assert mock_response["usage"]["total_tokens"] > 0
            
            # Validate captured request
            captured = self.inspector.get_captured_requests()[-1]
            
            resolution_results.append({
                "alias": alias,
                "resolution_time_ms": resolution_time * 1000,
                "model_resolved": captured.model == alias,
                "tier_correct": captured.tier == expected_tier,
                "priority_correct": captured.priority == expected_priority
            })
        
        # Validate all resolutions
        for result in resolution_results:
            assert result["model_resolved"], f"Model resolution failed for {result['alias']}"
            assert result["tier_correct"], f"Tier mismatch for {result['alias']}"
            assert result["priority_correct"], f"Priority mismatch for {result['alias']}"
            assert result["resolution_time_ms"] < 100, f"Resolution too slow for {result['alias']}"
        
        # Performance validation
        avg_resolution_time = sum(r["resolution_time_ms"] for r in resolution_results) / len(resolution_results)
        assert avg_resolution_time < 50, f"Average resolution time {avg_resolution_time:.2f}ms too slow"
    
    def test_mock_response_content_quality(self):
        """Test that mock responses are contextually appropriate"""
        
        test_cases = [
            {
                "model": "classification_premium",
                "task_type": "CLASSIFICATION",
                "expected_keys": ["classification", "confidence", "category"]
            },
            {
                "model": "extraction_premium", 
                "task_type": "EXTRACTION",
                "expected_keys": ["entities", "relationships"]
            },
            {
                "model": "synthesis_premium",
                "task_type": "SYNTHESIS",
                "expected_content": ["DSGVO", "BSI C5", "ISO 27001"]
            },
            {
                "model": "validation_primary_premium",
                "task_type": "VALIDATION",
                "expected_keys": ["validation_result", "confidence", "checks_performed"]
            }
        ]
        
        for test_case in test_cases:
            test_request = {
                "model": test_case["model"],
                "messages": [{"role": "user", "content": f"Test {test_case['task_type']}"}],
                "task_type": test_case["task_type"],
                "temperature": 0.1
            }
            
            mock_response = self.inspector.capture_request_callback(test_request)
            content = mock_response["choices"][0]["message"]["content"]
            
            # Test JSON responses
            if "expected_keys" in test_case:
                try:
                    content_json = json.loads(content)
                    for key in test_case["expected_keys"]:
                        assert key in content_json, f"Missing key {key} in {test_case['model']} response"
                except json.JSONDecodeError:
                    pytest.fail(f"Response from {test_case['model']} not valid JSON: {content}")
            
            # Test text responses
            if "expected_content" in test_case:
                for expected in test_case["expected_content"]:
                    assert expected in content, f"Missing content '{expected}' in {test_case['model']} response"
    
    def test_request_metadata_enhancement(self):
        """Test that requests are enhanced with enterprise metadata"""
        
        test_request = {
            "model": "extraction_premium",
            "messages": [
                {"role": "system", "content": "Extrahiere Entitäten aus dem folgenden Dokument"},
                {"role": "user", "content": "DSGVO Artikel 5 besagt, dass personenbezogene Daten rechtmäßig verarbeitet werden müssen."}
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
            "task_type": "EXTRACTION",
            "tier": "PREMIUM",
            "priority": 2,
            "pipeline_stage": "DOCUMENT_PROCESSING",
            "context_sources": ["UPLOADED_DOCUMENT", "KNOWLEDGE_GRAPH"]
        }
        
        mock_response = self.inspector.capture_request_callback(test_request)
        captured = self.inspector.get_captured_requests()[-1]
        
        # Validate all metadata was captured
        assert captured.model == "extraction_premium"
        assert captured.task_type == "EXTRACTION"
        assert captured.tier == "PREMIUM"
        assert captured.priority == 2
        assert captured.pipeline_stage == "DOCUMENT_PROCESSING"
        assert "UPLOADED_DOCUMENT" in captured.context_sources
        assert "KNOWLEDGE_GRAPH" in captured.context_sources
        assert captured.temperature == 0.2
        assert captured.max_tokens == 2000
        assert captured.response_format["type"] == "json_object"
        
        # Validate cost estimation
        assert captured.estimated_cost_usd > 0
        assert captured.request_size_bytes > 0
    
    def test_session_statistics_accuracy(self):
        """Test session statistics are calculated correctly"""
        
        # Execute multiple requests
        test_requests = [
            {"model": "classification_premium", "task_type": "CLASSIFICATION", "tier": "PREMIUM"},
            {"model": "extraction_balanced", "task_type": "EXTRACTION", "tier": "BALANCED"},
            {"model": "synthesis_cost_effective", "task_type": "SYNTHESIS", "tier": "COST_EFFECTIVE"},
            {"model": "validation_primary_premium", "task_type": "VALIDATION", "tier": "PREMIUM"}
        ]
        
        for req in test_requests:
            full_request = {
                **req,
                "messages": [{"role": "user", "content": f"Test {req['task_type']}"}],
                "temperature": 0.1
            }
            self.inspector.capture_request_callback(full_request)
        
        # Get statistics
        stats = self.inspector.get_session_statistics()
        
        # Validate statistics
        assert stats["total_requests"] == 4
        assert stats["task_types"]["CLASSIFICATION"] == 1
        assert stats["task_types"]["EXTRACTION"] == 1
        assert stats["task_types"]["SYNTHESIS"] == 1
        assert stats["task_types"]["VALIDATION"] == 1
        assert stats["tiers_used"]["PREMIUM"] == 2
        assert stats["tiers_used"]["BALANCED"] == 1
        assert stats["tiers_used"]["COST_EFFECTIVE"] == 1
        assert stats["total_estimated_cost_usd"] >= 0
        assert stats["average_request_size_bytes"] > 0


class TestK7EnterpriseOrchestrator:
    """K7 Enterprise Orchestrator Integration Tests"""
    
    @pytest.fixture(autouse=True)
    def setup_orchestrator(self):
        """Setup enterprise orchestrator for testing"""
        self.orchestrator = create_enterprise_orchestrator("test")
        yield
        # Cleanup handled by orchestrator
    
    @pytest.mark.asyncio
    async def test_infrastructure_validation(self):
        """Test infrastructure validation phase"""
        
        results = await self.orchestrator._validate_infrastructure()
        
        assert results["phase"] == "infrastructure"
        assert "services" in results
        assert "redis" in results["services"]
        assert results["services"]["redis"]["status"] in ["healthy", "failed"]
    
    @pytest.mark.asyncio
    async def test_request_interception_setup(self):
        """Test request interception setup phase"""
        
        results = await self.orchestrator._setup_request_interception()
        
        assert results["phase"] == "request_interception"
        assert "interception_test" in results
        assert results["interception_test"]["success"] == True
        assert results["interception_test"]["requests_captured"] > 0
        assert results["interception_test"]["mock_response_valid"] == True
    
    @pytest.mark.asyncio
    async def test_smart_alias_resolution_validation(self):
        """Test smart alias resolution validation phase"""
        
        results = await self.orchestrator._test_smart_alias_resolution()
        
        assert results["phase"] == "smart_alias_resolution"
        assert results["aliases_tested"] > 0
        assert "resolution_results" in results
        assert "performance_metrics" in results
        assert results["performance_metrics"]["success_rate_percentage"] > 90
        assert results["performance_metrics"]["average_resolution_time_ms"] < 100


# ===================================================================
# PERFORMANCE BENCHMARKS
# ===================================================================

def test_k7_performance_benchmarks():
    """Performance benchmarks for K7 validation"""
    
    inspector = create_test_session("k7_performance_test")
    
    # Test request capture overhead
    start_time = time.time()
    
    for i in range(100):
        test_request = {
            "model": f"test_model_{i % 5}",
            "messages": [{"role": "user", "content": f"Test request {i}"}],
            "temperature": 0.1
        }
        inspector.capture_request_callback(test_request)
    
    capture_time = time.time() - start_time
    avg_capture_time = capture_time / 100
    
    # Validate performance
    assert avg_capture_time < 0.01, f"Request capture too slow: {avg_capture_time:.4f}s per request"
    
    # Test session statistics performance
    start_time = time.time()
    stats = inspector.get_session_statistics()
    stats_time = time.time() - start_time
    
    assert stats_time < 0.1, f"Session statistics too slow: {stats_time:.4f}s"
    assert stats["total_requests"] == 100
    
    inspector.clear_session()


# ===================================================================
# CLI RUNNER FOR STANDALONE TESTING
# ===================================================================

if __name__ == "__main__":
    # Run tests directly
    import subprocess
    import sys
    
    # Run pytest on this file
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    sys.exit(result.returncode) 