#!/usr/bin/env python3
"""
Live Test für EnhancedModelManager
Testet die dynamische Modell-Auflösung mit der LiteLLM UI
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.enhanced_model_manager import (
    EnhancedModelManager, 
    TaskType, 
    ModelTier, 
    get_model_manager
)

async def test_model_resolution():
    """Test die Modell-Auflösung für alle Task-Types"""
    
    print("🧪 TESTING: EnhancedModelManager Live Integration")
    print("=" * 60)
    
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Test alle Task-Types
        test_cases = [
            (TaskType.CLASSIFICATION, ModelTier.PREMIUM),
            (TaskType.EXTRACTION, ModelTier.BALANCED),
            (TaskType.SYNTHESIS, ModelTier.COST_EFFECTIVE),
            (TaskType.VALIDATION_PRIMARY, ModelTier.PREMIUM),
            (TaskType.VALIDATION_SECONDARY, ModelTier.BALANCED),
        ]
        
        results = []
        
        for task_type, model_tier in test_cases:
            print(f"\n🔍 Testing: {task_type.value} (Tier: {model_tier.value})")
            
            try:
                model_config = await model_manager.get_model_for_task(
                    task_type=task_type,
                    model_tier=model_tier,
                    fallback=True
                )
                
                print(f"✅ Resolved Model: {model_config['model']}")
                print(f"   Alias: {model_config['model_alias']}")
                print(f"   Tier: {model_config['tier']}")
                print(f"   Strategy: {model_config['selection_strategy']}")
                print(f"   Selected At: {model_config['selected_at']}")
                
                results.append({
                    "task_type": task_type.value,
                    "requested_tier": model_tier.value,
                    "success": True,
                    **model_config
                })
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    "task_type": task_type.value,
                    "requested_tier": model_tier.value,
                    "success": False,
                    "error": str(e)
                })
        
        # Test Performance Stats
        print(f"\n📊 Performance Statistics:")
        stats = await model_manager.get_model_performance_stats()
        print(json.dumps(stats, indent=2))
        
        # Test Cache Refresh
        print(f"\n🔄 Testing Cache Refresh...")
        await model_manager.refresh_config_cache()
        print("✅ Cache refreshed successfully")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print("=" * 40)
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        print(f"✅ Successful resolutions: {successful}/{total}")
        
        if successful == total:
            print("🎉 ALL TESTS PASSED!")
            print("🚀 EnhancedModelManager is FULLY OPERATIONAL!")
        else:
            print("⚠️  Some tests failed - check configuration")
        
        # Clean up
        await model_manager.api_client.aclose()
        
        return results
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

async def main():
    """Main test function"""
    
    print(f"🕐 Test started at: {datetime.now().isoformat()}")
    
    results = await test_model_resolution()
    
    print(f"\n🕐 Test completed at: {datetime.now().isoformat()}")
    
    # Return appropriate exit code
    if results and all(r["success"] for r in results):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main()) 