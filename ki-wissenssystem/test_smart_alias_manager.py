#!/usr/bin/env python3
"""
Smart Alias Strategy Test Suite
Tests the new Smart Alias implementation with EnhancedModelManager

Features Tested:
- 25 Task-Profile combinations resolved correctly
- Profile compatibility matrix working
- Legacy fallback support
- Performance tracking
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.enhanced_model_manager import (
    EnhancedModelManager, 
    TaskType, 
    ModelTier, 
    get_model_manager
)

def print_header(title: str, char: str = "="):
    """Print a formatted header"""
    print(f"\n{char * 60}")
    print(f"🎯 {title}")
    print(f"{char * 60}")

def print_result(success: bool, message: str):
    """Print a formatted test result"""
    icon = "✅" if success else "❌"
    status = "SUCCESS" if success else "FAILED"
    print(f"{icon} {status}: {message}")

async def test_smart_alias_resolution():
    """Test Smart Alias resolution for all task-profile combinations"""
    
    print_header("SMART ALIAS STRATEGY - COMPREHENSIVE TEST", "=")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get model manager
        model_manager = await get_model_manager()
        print_result(True, "EnhancedModelManager initialized successfully")
        
        # Test Matrix: All 5 Tasks × 5 Profiles = 25 combinations
        test_matrix = [
            # Classification Tests
            (TaskType.CLASSIFICATION, ModelTier.PREMIUM),
            (TaskType.CLASSIFICATION, ModelTier.BALANCED),
            (TaskType.CLASSIFICATION, ModelTier.COST_EFFECTIVE),
            (TaskType.CLASSIFICATION, ModelTier.SPECIALIZED),
            (TaskType.CLASSIFICATION, ModelTier.ULTRA_FAST),
            
            # Extraction Tests
            (TaskType.EXTRACTION, ModelTier.PREMIUM),
            (TaskType.EXTRACTION, ModelTier.BALANCED),
            (TaskType.EXTRACTION, ModelTier.COST_EFFECTIVE),
            (TaskType.EXTRACTION, ModelTier.SPECIALIZED),
            (TaskType.EXTRACTION, ModelTier.ULTRA_FAST),
            
            # Synthesis Tests
            (TaskType.SYNTHESIS, ModelTier.PREMIUM),
            (TaskType.SYNTHESIS, ModelTier.BALANCED),
            (TaskType.SYNTHESIS, ModelTier.COST_EFFECTIVE),
            (TaskType.SYNTHESIS, ModelTier.SPECIALIZED),
            (TaskType.SYNTHESIS, ModelTier.ULTRA_FAST),
            
            # Validation Primary Tests
            (TaskType.VALIDATION_PRIMARY, ModelTier.PREMIUM),
            (TaskType.VALIDATION_PRIMARY, ModelTier.BALANCED),
            (TaskType.VALIDATION_PRIMARY, ModelTier.COST_EFFECTIVE),
            (TaskType.VALIDATION_PRIMARY, ModelTier.SPECIALIZED),
            (TaskType.VALIDATION_PRIMARY, ModelTier.ULTRA_FAST),
            
            # Validation Secondary Tests
            (TaskType.VALIDATION_SECONDARY, ModelTier.PREMIUM),
            (TaskType.VALIDATION_SECONDARY, ModelTier.BALANCED),
            (TaskType.VALIDATION_SECONDARY, ModelTier.COST_EFFECTIVE),
            (TaskType.VALIDATION_SECONDARY, ModelTier.SPECIALIZED),
            (TaskType.VALIDATION_SECONDARY, ModelTier.ULTRA_FAST),
        ]
        
        print_header("25 SMART ALIAS RESOLUTION TESTS", "-")
        
        results = []
        exact_matches = 0
        profile_fallbacks = 0
        legacy_fallbacks = 0
        static_fallbacks = 0
        
        for i, (task_type, model_tier) in enumerate(test_matrix, 1):
            expected_alias = f"{task_type.value}_{model_tier.value}"
            
            try:
                model_config = await model_manager.get_model_for_task(
                    task_type=task_type,
                    model_tier=model_tier,
                    fallback=True
                )
                
                match_type = model_config.get("match_type", "unknown")
                resolved_alias = model_config["model_alias"]
                provider_model = model_config["model"]
                selection_strategy = model_config["selection_strategy"]
                
                # Categorize result type
                if match_type == "exact_smart_alias":
                    exact_matches += 1
                    result_icon = "🎯"
                elif match_type == "same_task_different_profile":
                    profile_fallbacks += 1
                    result_icon = "🔄"
                elif match_type == "legacy_format":
                    legacy_fallbacks += 1
                    result_icon = "📰"  
                else:
                    static_fallbacks += 1
                    result_icon = "⚠️"
                
                print(f"{result_icon} Test {i:2d}/25: {expected_alias:30} → {resolved_alias:30} ({provider_model}) [{match_type}]")
                
                results.append({
                    "test_number": i,
                    "task_type": task_type.value,
                    "requested_tier": model_tier.value,
                    "expected_alias": expected_alias,
                    "resolved_alias": resolved_alias,
                    "provider_model": provider_model,
                    "match_type": match_type,
                    "selection_strategy": selection_strategy,
                    "success": True
                })
                
            except Exception as e:
                print_result(False, f"Test {i:2d}/25: {expected_alias} → ERROR: {e}")
                results.append({
                    "test_number": i,
                    "task_type": task_type.value,
                    "requested_tier": model_tier.value,
                    "expected_alias": expected_alias,
                    "success": False,
                    "error": str(e)
                })
        
        # Test Summary Statistics
        print_header("TEST SUMMARY STATISTICS", "-")
        
        successful_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"📊 Total Tests:           {total_tests}")
        print(f"✅ Successful:           {successful_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed:               {total_tests - successful_tests}")
        print(f"\n🎯 Exact Smart Matches:  {exact_matches}")
        print(f"🔄 Profile Fallbacks:    {profile_fallbacks}")
        print(f"📰 Legacy Fallbacks:     {legacy_fallbacks}")
        print(f"⚠️  Static Fallbacks:    {static_fallbacks}")
        
        # Test Performance Statistics
        print_header("PERFORMANCE TRACKING TEST", "-")
        
        try:
            performance_stats = await model_manager.get_model_performance_stats()
            print(f"📈 Performance tracking models: {len(performance_stats)}")
            
            for model_name, stats in performance_stats.items():
                print(f"   • {model_name}: {stats['selections']} selections, tasks: {stats['task_types']}")
        
        except Exception as e:
            print_result(False, f"Performance stats retrieval failed: {e}")
        
        # Test Cache Refresh
        print_header("CACHE REFRESH TEST", "-")
        
        try:
            await model_manager.refresh_config_cache()
            print_result(True, "Configuration cache refreshed successfully")
        except Exception as e:
            print_result(False, f"Cache refresh failed: {e}")
        
        # Overall Assessment
        print_header("SMART ALIAS STRATEGY ASSESSMENT", "=")
        
        if success_rate >= 95:
            assessment = "EXCELLENT ✨"
            recommendation = "Smart Alias Strategy is production-ready!"
        elif success_rate >= 80:
            assessment = "GOOD ✅"
            recommendation = "Smart Alias Strategy working well with minor optimizations needed."
        elif success_rate >= 60:
            assessment = "ACCEPTABLE ⚠️"
            recommendation = "Smart Alias Strategy needs improvements before production."
        else:
            assessment = "NEEDS WORK ❌"
            recommendation = "Smart Alias Strategy requires significant fixes."
        
        print(f"🏆 Overall Grade: {assessment}")
        print(f"📝 Recommendation: {recommendation}")
        print(f"🎯 Exact Match Rate: {(exact_matches/total_tests)*100:.1f}%")
        print(f"🔄 Intelligent Fallback Rate: {(profile_fallbacks/total_tests)*100:.1f}%")
        
        # Export detailed results
        results_file = "smart_alias_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_timestamp": datetime.now().isoformat(),
                "test_summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": success_rate,
                    "exact_matches": exact_matches,
                    "profile_fallbacks": profile_fallbacks,
                    "legacy_fallbacks": legacy_fallbacks,
                    "static_fallbacks": static_fallbacks
                },
                "detailed_results": results,
                "performance_stats": performance_stats if 'performance_stats' in locals() else {}
            }, indent=2)
        
        print(f"\n📄 Detailed results exported to: {results_file}")
        
        return success_rate >= 80  # Return True if success rate is acceptable
        
    except Exception as e:
        print_result(False, f"Critical test failure: {e}")
        return False

async def main():
    """Main test execution"""
    
    print("🚀 Starting Smart Alias Strategy Test Suite...")
    
    try:
        success = await test_smart_alias_resolution()
        
        if success:
            print("\n🎉 SMART ALIAS STRATEGY: IMPLEMENTATION SUCCESSFUL!")
            exit_code = 0
        else:
            print("\n💥 SMART ALIAS STRATEGY: IMPLEMENTATION NEEDS WORK!")
            exit_code = 1
            
    except Exception as e:
        print(f"\n💥 TEST SUITE FAILED: {e}")
        exit_code = 1
    
    print(f"\n🏁 Test suite completed with exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 