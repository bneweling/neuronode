#!/usr/bin/env python3
"""
LiteLLM Profile System Integration Test
Testet die vollständige Profile-basierte Model-Routing Funktionalität
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import logging
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProfileSystemTester:
    """Test Suite für LiteLLM Profile System"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", litellm_base_url: str = "http://localhost:4000"):
        self.api_base_url = api_base_url
        self.litellm_base_url = litellm_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Test Results
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_all_tests(self):
        """Führt alle Profile-System Tests durch"""
        logger.info("🎯 Starting LiteLLM Profile System Integration Tests")
        
        try:
            # Test 1: Profile Manager API Tests
            await self.test_profile_api_endpoints()
            
            # Test 2: Profile Configuration Tests
            await self.test_profile_configuration()
            
            # Test 3: Profile Switching Tests
            await self.test_profile_switching()
            
            # Test 4: Task-Alias Integration Tests
            await self.test_task_alias_integration()
            
            # Test 5: End-to-End Profile Workflow Tests
            await self.test_e2e_profile_workflow()
            
            # Final Report
            await self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return False
        
        finally:
            await self.client.aclose()
            
        return self.results["failed_tests"] == 0
    
    async def test_profile_api_endpoints(self):
        """Test 1: Profile Management API Endpoints"""
        logger.info("📡 Testing Profile Management API Endpoints")
        
        # Test 1.1: List Available Profiles
        await self._test_api_call(
            "GET /admin/profiles/list",
            "GET",
            f"{self.api_base_url}/admin/profiles/list",
            expected_keys=["profiles", "total_profiles"]
        )
        
        # Test 1.2: Get Current Profile Status
        await self._test_api_call(
            "GET /admin/profiles/status",
            "GET", 
            f"{self.api_base_url}/admin/profiles/status",
            expected_keys=["active_profile", "active_mappings", "mapping_valid"]
        )
        
        # Test 1.3: Validate Profile Assignments
        await self._test_api_call(
            "GET /admin/profiles/validate",
            "GET",
            f"{self.api_base_url}/admin/profiles/validate",
            expected_keys=["validation_results", "summary"]
        )
        
        # Test 1.4: Get Profile Configuration
        await self._test_api_call(
            "GET /admin/profiles/config",
            "GET",
            f"{self.api_base_url}/admin/profiles/config",
            expected_keys=["configuration"]
        )
    
    async def test_profile_configuration(self):
        """Test 2: Profile Configuration Validation"""
        logger.info("⚙️ Testing Profile Configuration")
        
        try:
            # Test 2.1: Check LiteLLM Config File
            config_path = project_root / "litellm_config.yaml"
            if not config_path.exists():
                raise FileNotFoundError(f"LiteLLM config not found: {config_path}")
            
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate Profile Settings
            profile_settings = config.get('profile_settings', {})
            self._assert_test(
                "Profile settings exist",
                'available_profiles' in profile_settings,
                f"Profile settings missing in config: {list(profile_settings.keys())}"
            )
            
            # Validate model_group_alias
            router_settings = config.get('router_settings', {})
            self._assert_test(
                "model_group_alias exists", 
                'model_group_alias' in router_settings,
                f"model_group_alias missing in router_settings: {list(router_settings.keys())}"
            )
            
            # Test 2.2: Validate Profile Completeness
            required_profiles = ["premium", "balanced", "cost_effective", "specialized", "ultra_fast"]
            available_profiles = profile_settings.get('available_profiles', {})
            
            for profile in required_profiles:
                self._assert_test(
                    f"Profile {profile} exists",
                    profile in available_profiles,
                    f"Missing profile: {profile}"
                )
            
            # Test 2.3: Validate Task-Alias Mappings
            model_group_alias = router_settings.get('model_group_alias', {})
            required_tasks = ["classification", "extraction", "synthesis", "validation_primary", "validation_secondary"]
            
            for task in required_tasks:
                self._assert_test(
                    f"Task alias {task} exists",
                    task in model_group_alias,
                    f"Missing task alias: {task}"
                )
            
            logger.info("✅ Profile configuration validation passed")
            
        except Exception as e:
            self._record_test_failure("Profile Configuration Test", str(e))
    
    async def test_profile_switching(self):
        """Test 3: Profile Switching Functionality"""
        logger.info("🔄 Testing Profile Switching")
        
        profiles_to_test = ["balanced", "premium", "cost_effective"]
        
        for profile in profiles_to_test:
            try:
                # Test 3.1: Switch to Profile
                switch_response = await self._test_api_call(
                    f"POST /admin/profiles/switch (profile: {profile})",
                    "POST",
                    f"{self.api_base_url}/admin/profiles/switch",
                    json_data={"profile": profile},
                    expected_keys=["success", "to_profile", "active_mappings"]
                )
                
                if switch_response and switch_response.get("success"):
                    # Test 3.2: Verify Profile is Active
                    await asyncio.sleep(1)  # Allow time for config update
                    
                    status_response = await self._test_api_call(
                        f"Verify {profile} is active",
                        "GET",
                        f"{self.api_base_url}/admin/profiles/status"
                    )
                    
                    if status_response:
                        active_profile = status_response.get("active_profile")
                        self._assert_test(
                            f"Profile {profile} is active",
                            active_profile == profile,
                            f"Expected {profile}, got {active_profile}"
                        )
                
            except Exception as e:
                self._record_test_failure(f"Profile Switch to {profile}", str(e))
    
    async def test_task_alias_integration(self):
        """Test 4: Task-Alias Integration"""
        logger.info("🎯 Testing Task-Alias Integration")
        
        try:
            # Test 4.1: Import and Test ProfileManager
            from src.llm.profile_manager import ProfileManager
            
            profile_manager = ProfileManager(config_path=str(project_root / "litellm_config.yaml"))
            
            # Test 4.2: Test Profile Manager Methods
            current_profile = await profile_manager.get_current_profile()
            self._assert_test(
                "ProfileManager.get_current_profile() works",
                "active_profile" in current_profile,
                f"Missing active_profile in response: {list(current_profile.keys())}"
            )
            
            # Test 4.3: Test LiteLLMClient Task-Alias Integration
            from src.llm.litellm_client import LiteLLMClient
            
            client = LiteLLMClient()
            
            # Test Task-Alias Mapping
            test_tasks = ["classification", "extraction", "synthesis"]
            for task in test_tasks:
                task_alias = client.get_task_alias(task)
                self._assert_test(
                    f"Task alias for {task}",
                    task_alias == task,
                    f"Expected {task}, got {task_alias}"
                )
            
            logger.info("✅ Task-Alias integration tests passed")
            
        except Exception as e:
            self._record_test_failure("Task-Alias Integration", str(e))
    
    async def test_e2e_profile_workflow(self):
        """Test 5: End-to-End Profile Workflow"""
        logger.info("🌟 Testing End-to-End Profile Workflow")
        
        try:
            # Test 5.1: Full Profile Switch Workflow
            test_profile = "balanced"
            
            # Switch Profile
            logger.info(f"Switching to profile: {test_profile}")
            switch_response = await self.client.post(
                f"{self.api_base_url}/admin/profiles/switch",
                json={"profile": test_profile}
            )
            
            self._assert_test(
                "E2E Profile switch successful",
                switch_response.status_code == 200,
                f"Switch failed with status {switch_response.status_code}"
            )
            
            # Verify Switch
            await asyncio.sleep(2)  # Allow config propagation
            
            status_response = await self.client.get(f"{self.api_base_url}/admin/profiles/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                self._assert_test(
                    "E2E Profile is correctly active",
                    status_data.get("active_profile") == test_profile,
                    f"Profile not switched correctly: {status_data.get('active_profile')}"
                )
                
                # Test 5.2: Validate Model Mappings
                active_mappings = status_data.get("active_mappings", {})
                expected_tasks = ["classification", "extraction", "synthesis"]
                
                for task in expected_tasks:
                    expected_smart_alias = f"{task}_{test_profile}"
                    actual_smart_alias = active_mappings.get(task)
                    
                    self._assert_test(
                        f"E2E {task} mapped to {expected_smart_alias}",
                        actual_smart_alias == expected_smart_alias,
                        f"Expected {expected_smart_alias}, got {actual_smart_alias}"
                    )
            
            logger.info("✅ End-to-End workflow tests passed")
            
        except Exception as e:
            self._record_test_failure("End-to-End Workflow", str(e))
    
    async def _test_api_call(self, test_name: str, method: str, url: str, json_data=None, expected_keys=None):
        """Helper für API Call Tests"""
        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            self._assert_test(
                f"{test_name} - HTTP Status",
                response.status_code in [200, 201],
                f"HTTP {response.status_code}: {response.text}"
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                if expected_keys:
                    for key in expected_keys:
                        self._assert_test(
                            f"{test_name} - Key '{key}' exists",
                            key in data,
                            f"Missing key '{key}' in response: {list(data.keys())}"
                        )
                
                logger.info(f"✅ {test_name} passed")
                return data
            
        except Exception as e:
            self._record_test_failure(test_name, str(e))
            return None
    
    def _assert_test(self, test_name: str, condition: bool, error_message: str = ""):
        """Helper für Test Assertions"""
        self.results["total_tests"] += 1
        
        if condition:
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": test_name,
                "status": "PASSED",
                "message": "OK"
            })
        else:
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": test_name,
                "status": "FAILED", 
                "message": error_message
            })
            logger.error(f"❌ {test_name}: {error_message}")
    
    def _record_test_failure(self, test_name: str, error_message: str):
        """Helper für Test Failure Recording"""
        self._assert_test(test_name, False, error_message)
    
    async def generate_test_report(self):
        """Generates final test report"""
        logger.info("\n" + "="*60)
        logger.info("🎯 LITELLM PROFILE SYSTEM TEST REPORT")
        logger.info("="*60)
        
        logger.info(f"Total Tests: {self.results['total_tests']}")
        logger.info(f"Passed: {self.results['passed_tests']}")
        logger.info(f"Failed: {self.results['failed_tests']}")
        
        if self.results['failed_tests'] == 0:
            logger.info("🎉 ALL TESTS PASSED! Profile System is ready for production.")
        else:
            logger.error(f"❌ {self.results['failed_tests']} tests failed. Review required.")
        
        # Save detailed report
        report_path = project_root / "profile_system_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Detailed report saved: {report_path}")
        logger.info("="*60)

async def main():
    """Main test execution"""
    tester = ProfileSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🚀 Profile System is ready for production!")
        sys.exit(0)
    else:
        logger.error("💥 Profile System has issues that need to be resolved.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 