#!/usr/bin/env python3
"""
Performance Benchmark für Enhanced Intent Analyzer
KI-Wissenssystem - LiteLLM v1.72.6 Migration

ZIEL: Validierung des Sub-200ms Performance-Targets
COVERAGE: Verschiedene Query-Typen und Komplexitätsgrade
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any
from datetime import datetime
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.retrievers.intent_analyzer import EnhancedIntentAnalyzer, QueryIntent

class IntentAnalyzerBenchmark:
    """Performance-Benchmark für Intent Analyzer Migration"""
    
    def __init__(self):
        self.analyzer = EnhancedIntentAnalyzer()
        self.benchmark_results = {
            "test_start": datetime.now().isoformat(),
            "test_queries": [],
            "performance_stats": {},
            "target_validation": {},
            "overall_results": {}
        }
        
        # Test-Queries verschiedener Komplexitätsgrade
        self.test_queries = [
            # Simple queries (Expected: <100ms)
            {
                "query": "Was ist MFA?",
                "expected_intent": QueryIntent.GENERAL_INFORMATION,
                "complexity": "simple",
                "target_time_ms": 100
            },
            {
                "query": "BSI C5",
                "expected_intent": QueryIntent.GENERAL_INFORMATION,
                "complexity": "simple",
                "target_time_ms": 100
            },
            
            # Medium complexity queries (Expected: <150ms)
            {
                "query": "Wie implementiere ich MFA in Azure?",
                "expected_intent": QueryIntent.TECHNICAL_IMPLEMENTATION,
                "complexity": "medium",
                "target_time_ms": 150
            },
            {
                "query": "Was fordert BSI C5 zu Backup-Verfahren?",
                "expected_intent": QueryIntent.COMPLIANCE_REQUIREMENT,
                "complexity": "medium", 
                "target_time_ms": 150
            },
            {
                "query": "Best Practices für Verschlüsselung",
                "expected_intent": QueryIntent.BEST_PRACTICE,
                "complexity": "medium",
                "target_time_ms": 150
            },
            
            # Complex queries (Expected: <200ms)
            {
                "query": "Wie verhält sich BSI IT-Grundschutz OPS-01 zu ISO 27001 A.12.6.1 bezüglich technischer Schwachstellenverwaltung und Patch-Management in hybriden Cloud-Umgebungen mit Azure und AWS?",
                "expected_intent": QueryIntent.MAPPING_COMPARISON,
                "complexity": "complex",
                "target_time_ms": 200
            },
            {
                "query": "Vergleich zwischen BSI C5 CCM-12 und NIST CSF Identity Management Requirements mit technischer Implementierung in Active Directory und Entra ID",
                "expected_intent": QueryIntent.MAPPING_COMPARISON,
                "complexity": "complex",
                "target_time_ms": 200
            },
            
            # Edge cases
            {
                "query": "GDPR DSGVO Compliance BSI C5 ISO 27001 NIST SOC 2 PCI DSS Azure AWS GCP Docker Kubernetes",
                "expected_intent": QueryIntent.GENERAL_INFORMATION,
                "complexity": "edge_case",
                "target_time_ms": 200
            }
        ]
    
    async def run_benchmark(self, iterations: int = 5) -> Dict[str, Any]:
        """Führt vollständigen Performance-Benchmark durch"""
        
        print("🚀 Starting Intent Analyzer Performance Benchmark")
        print(f"📊 Testing {len(self.test_queries)} query types with {iterations} iterations each")
        print("-" * 80)
        
        all_results = []
        
        for query_test in self.test_queries:
            print(f"\n🎯 Testing: {query_test['query'][:60]}...")
            print(f"   Expected: {query_test['expected_intent'].value} | Complexity: {query_test['complexity']} | Target: {query_test['target_time_ms']}ms")
            
            query_results = []
            
            # Run multiple iterations for statistical accuracy
            for iteration in range(iterations):
                result = await self._benchmark_single_query(query_test['query'], iteration + 1)
                query_results.append(result)
                
                # Progress indicator
                print(f"   Iteration {iteration + 1}: {result['response_time_ms']:.1f}ms - {result['intent']}")
            
            # Calculate statistics for this query
            response_times = [r['response_time_ms'] for r in query_results]
            query_stats = {
                "query": query_test['query'],
                "expected_intent": query_test['expected_intent'].value,
                "complexity": query_test['complexity'],
                "target_time_ms": query_test['target_time_ms'],
                "iterations": iterations,
                "results": query_results,
                "statistics": {
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "avg_ms": statistics.mean(response_times),
                    "median_ms": statistics.median(response_times),
                    "std_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0.0
                },
                "target_met": all(t <= query_test['target_time_ms'] for t in response_times),
                "intent_accuracy": sum(1 for r in query_results if r['intent'] == query_test['expected_intent'].value) / iterations
            }
            
            all_results.append(query_stats)
            
            # Print summary for this query
            print(f"   📊 Stats: Avg={query_stats['statistics']['avg_ms']:.1f}ms, "
                  f"Min={query_stats['statistics']['min_ms']:.1f}ms, "
                  f"Max={query_stats['statistics']['max_ms']:.1f}ms")
            print(f"   ✅ Target Met: {query_stats['target_met']} | Intent Accuracy: {query_stats['intent_accuracy']:.1%}")
        
        # Overall benchmark results
        self.benchmark_results["test_queries"] = all_results
        self.benchmark_results["performance_stats"] = self.analyzer.get_performance_stats()
        
        # Calculate overall statistics
        all_response_times = []
        target_met_count = 0
        intent_accuracy_scores = []
        
        for query_result in all_results:
            all_response_times.extend([r['response_time_ms'] for r in query_result['results']])
            if query_result['target_met']:
                target_met_count += 1
            intent_accuracy_scores.append(query_result['intent_accuracy'])
        
        overall_stats = {
            "total_queries_tested": len(self.test_queries),
            "total_iterations": len(all_response_times),
            "overall_response_time": {
                "min_ms": min(all_response_times),
                "max_ms": max(all_response_times),
                "avg_ms": statistics.mean(all_response_times),
                "median_ms": statistics.median(all_response_times),
                "p95_ms": self._percentile(all_response_times, 95),
                "p99_ms": self._percentile(all_response_times, 99)
            },
            "target_validation": {
                "queries_meeting_target": target_met_count,
                "total_queries": len(self.test_queries),
                "success_rate": target_met_count / len(self.test_queries),
                "sub_200ms_rate": sum(1 for t in all_response_times if t <= 200) / len(all_response_times)
            },
            "intent_accuracy": {
                "avg_accuracy": statistics.mean(intent_accuracy_scores),
                "min_accuracy": min(intent_accuracy_scores),
                "max_accuracy": max(intent_accuracy_scores)
            }
        }
        
        self.benchmark_results["overall_results"] = overall_stats
        self.benchmark_results["test_end"] = datetime.now().isoformat()
        
        return self.benchmark_results
    
    async def _benchmark_single_query(self, query: str, iteration: int) -> Dict[str, Any]:
        """Benchmark einer einzelnen Query"""
        
        start_time = time.time()
        
        try:
            analysis = await self.analyzer.analyze_query(query)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                "iteration": iteration,
                "query": query,
                "response_time_ms": response_time_ms,
                "intent": analysis.primary_intent.value,
                "entities_count": len(analysis.entities),
                "confidence": analysis.confidence,
                "complexity_score": analysis.complexity_score,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                "iteration": iteration,
                "query": query,
                "response_time_ms": response_time_ms,
                "intent": "ERROR",
                "entities_count": 0,
                "confidence": 0.0,
                "complexity_score": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def print_detailed_report(self):
        """Druckt detaillierten Benchmark-Report"""
        
        results = self.benchmark_results
        overall = results["overall_results"]
        
        print("\n" + "=" * 80)
        print("🎯 INTENT ANALYZER PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Total Tests: {overall['total_iterations']} iterations across {overall['total_queries_tested']} query types")
        print(f"   Average Response Time: {overall['overall_response_time']['avg_ms']:.1f}ms")
        print(f"   Median Response Time: {overall['overall_response_time']['median_ms']:.1f}ms")
        print(f"   95th Percentile: {overall['overall_response_time']['p95_ms']:.1f}ms")
        print(f"   99th Percentile: {overall['overall_response_time']['p99_ms']:.1f}ms")
        
        print(f"\n🎯 TARGET VALIDATION:")
        print(f"   Sub-200ms Success Rate: {overall['target_validation']['sub_200ms_rate']:.1%}")
        print(f"   Queries Meeting Individual Targets: {overall['target_validation']['queries_meeting_target']}/{overall['target_validation']['total_queries']}")
        print(f"   Overall Target Success Rate: {overall['target_validation']['success_rate']:.1%}")
        
        print(f"\n🎯 INTENT ACCURACY:")
        print(f"   Average Intent Accuracy: {overall['intent_accuracy']['avg_accuracy']:.1%}")
        print(f"   Min Intent Accuracy: {overall['intent_accuracy']['min_accuracy']:.1%}")
        print(f"   Max Intent Accuracy: {overall['intent_accuracy']['max_accuracy']:.1%}")
        
        # Performance by complexity
        print(f"\n📈 PERFORMANCE BY COMPLEXITY:")
        complexity_stats = {}
        
        for query_result in results["test_queries"]:
            complexity = query_result["complexity"]
            if complexity not in complexity_stats:
                complexity_stats[complexity] = []
            complexity_stats[complexity].append(query_result["statistics"]["avg_ms"])
        
        for complexity, times in complexity_stats.items():
            avg_time = statistics.mean(times)
            print(f"   {complexity.upper()}: {avg_time:.1f}ms average")
        
        # Service statistics
        if "performance_stats" in results:
            service_stats = results["performance_stats"]
            print(f"\n🔧 SERVICE STATISTICS:")
            print(f"   Total Analyses: {service_stats.get('total_analyses', 0)}")
            print(f"   Service Avg Response Time: {service_stats.get('avg_response_time_ms', 0):.1f}ms")
            print(f"   Pattern Match Rate: {service_stats.get('pattern_match_rate', 0):.1%}")
            print(f"   LLM Fallback Rate: {service_stats.get('llm_fallback_rate', 0):.1%}")
            print(f"   Performance Target Met: {service_stats.get('performance_target_met', False)}")
        
        print(f"\n✅ BENCHMARK CONCLUSION:")
        sub_200ms_rate = overall['target_validation']['sub_200ms_rate']
        if sub_200ms_rate >= 0.95:
            print(f"   🎉 EXCELLENT: {sub_200ms_rate:.1%} of queries under 200ms - Performance target EXCEEDED!")
        elif sub_200ms_rate >= 0.90:
            print(f"   ✅ GOOD: {sub_200ms_rate:.1%} of queries under 200ms - Performance target MET!")
        elif sub_200ms_rate >= 0.80:
            print(f"   ⚠️  ACCEPTABLE: {sub_200ms_rate:.1%} of queries under 200ms - Performance target mostly met")
        else:
            print(f"   ❌ NEEDS IMPROVEMENT: {sub_200ms_rate:.1%} of queries under 200ms - Performance target not met")
    
    def save_results(self, filename: str = None):
        """Speichert Benchmark-Ergebnisse als JSON"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intent_analyzer_benchmark_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.benchmark_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Benchmark results saved to: {filename}")

async def main():
    """Hauptfunktion für Performance-Benchmark"""
    
    benchmark = IntentAnalyzerBenchmark()
    
    # Run benchmark
    print("Initializing Intent Analyzer Performance Benchmark...")
    results = await benchmark.run_benchmark(iterations=3)  # 3 iterations for speed
    
    # Print detailed report
    benchmark.print_detailed_report()
    
    # Save results
    benchmark.save_results()
    
    # Validate critical performance requirement
    overall = results["overall_results"]
    sub_200ms_rate = overall['target_validation']['sub_200ms_rate']
    
    if sub_200ms_rate >= 0.90:
        print(f"\n🎉 PERFORMANCE VALIDATION: SUCCESS - {sub_200ms_rate:.1%} sub-200ms rate exceeds requirement!")
        return 0
    else:
        print(f"\n❌ PERFORMANCE VALIDATION: FAILED - {sub_200ms_rate:.1%} sub-200ms rate below 90% requirement")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 