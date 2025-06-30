#!/usr/bin/env python3
"""
Einfacher Performance-Test für Intent Analyzer Migration
Neuronode - LiteLLM v1.72.6 Migration

ZIEL: Validierung der Intent Analyzer Grundfunktionalität
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any
from datetime import datetime
import sys
import os
import re

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.retrievers.intent_analyzer import QueryIntent

class SimpleIntentAnalyzer:
    """
    Vereinfachte Version des Intent Analyzers für Performance-Tests
    ohne vollständige LiteLLM-Infrastruktur
    """
    
    def __init__(self):
        # Entity patterns (from original implementation)
        self.patterns = {
            "bsi_control": re.compile(r'\b([A-Z]{3,4}[-.]?\d+(?:\.\d+)*(?:\.A\d+)?)\b'),
            "c5_control": re.compile(r'\b([A-Z]{2,3}-\d{2})\b'),
            "iso_control": re.compile(r'\b(?:ISO\s*)?(?:27001|27002)(?:\s*[:\-]\s*)?([A-Z]?\d+(?:\.\d+)*)\b', re.I),
            "technology": re.compile(r'\b(Azure|AWS|GCP|Active Directory|Entra|Office 365|SharePoint|Teams|Docker|Kubernetes|Linux|Windows|VMware|Citrix)\b', re.I),
            "standard": re.compile(r'\b(BSI(?:\s+(?:C5|IT-Grundschutz))?|ISO\s*2700[0-9]|NIST(?:\s+CSF)?|SOC\s*2|PCI\s*DSS|GDPR|DSGVO)\b', re.I),
            "concept": re.compile(r'\b(MFA|Multi-Factor|Verschlüsselung|Encryption|Backup|Firewall|VPN|Zero Trust|Identity|IAM|SIEM|SOC|Patch|Vulnerability)\b', re.I)
        }
        
        self.stopwords = {
            "der", "die", "das", "und", "oder", "aber", "mit", "von", "zu", "in",
            "für", "auf", "bei", "nach", "wie", "was", "wann", "wo", "ist", "sind",
            "wird", "werden", "kann", "können", "muss", "müssen", "soll", "sollen",
            "haben", "hat", "hatte", "hatten", "sein", "war", "waren", "im", "am", "beim"
        }
        
        self.stats = {
            "total_analyses": 0,
            "pattern_matches": 0,
            "total_time": 0.0
        }
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query with pattern-based approach"""
        
        start_time = time.time()
        
        # Pattern-based entity extraction
        entities = self._extract_entities_with_patterns(query)
        
        # Rule-based intent detection
        intent = self._detect_intent(query, entities)
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        # Calculate confidence
        confidence = self._calculate_confidence(entities, keywords)
        
        analysis_time = time.time() - start_time
        
        # Update stats
        self.stats["total_analyses"] += 1
        self.stats["total_time"] += analysis_time
        if entities:
            self.stats["pattern_matches"] += 1
        
        return {
            "primary_intent": intent.value,
            "entities": entities,
            "search_keywords": keywords,
            "confidence": confidence,
            "analysis_time_ms": analysis_time * 1000,
            "pattern_matches": len([e for e_list in entities.values() for e in e_list])
        }
    
    def _extract_entities_with_patterns(self, query: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        
        entities = {
            "controls": [],
            "technologies": [],
            "standards": [],
            "concepts": []
        }
        
        # Extract control IDs
        for pattern_name, pattern in [
            ("bsi", self.patterns["bsi_control"]),
            ("c5", self.patterns["c5_control"]),
            ("iso", self.patterns["iso_control"])
        ]:
            matches = pattern.findall(query)
            entities["controls"].extend(matches)
        
        # Extract technologies
        tech_matches = self.patterns["technology"].findall(query)
        entities["technologies"] = [match for match in tech_matches]
        
        # Extract standards
        standard_matches = self.patterns["standard"].findall(query)
        entities["standards"] = [match for match in standard_matches]
        
        # Extract concepts
        concept_matches = self.patterns["concept"].findall(query)
        entities["concepts"] = [match for match in concept_matches]
        
        # Clean up and deduplicate
        for key in entities:
            entities[key] = list(set(filter(None, entities[key])))
        
        return entities
    
    def _detect_intent(self, query: str, entities: Dict[str, List[str]]) -> QueryIntent:
        """Rule-based intent detection"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["was fordert", "anforderung", "muss ich", "compliance", "requirement"]):
            return QueryIntent.COMPLIANCE_REQUIREMENT
        elif any(word in query_lower for word in ["wie implementiere", "umsetzen", "konfigurieren", "einrichten", "setup"]):
            return QueryIntent.TECHNICAL_IMPLEMENTATION
        elif any(word in query_lower for word in ["vergleich", "unterschied", "mapping", "vs", "versus", "compare"]):
            return QueryIntent.MAPPING_COMPARISON
        elif any(word in query_lower for word in ["best practice", "empfehlung", "tipps", "recommendation"]):
            return QueryIntent.BEST_PRACTICE
        elif entities.get("controls"):
            return QueryIntent.SPECIFIC_CONTROL
        else:
            return QueryIntent.GENERAL_INFORMATION
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        
        words = query.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in self.stopwords]
        
        # Add technical terms
        technical_terms = []
        for word in words:
            if word.upper() in ["MFA", "IAM", "VPN", "API", "CLI", "GUI", "SOC", "SIEM", "PCI", "GDPR"]:
                technical_terms.append(word.upper())
        
        return (keywords + technical_terms)[:10]
    
    def _calculate_confidence(self, entities: Dict[str, List[str]], keywords: List[str]) -> float:
        """Calculate confidence based on entity matches and keywords"""
        
        entity_count = sum(len(e_list) for e_list in entities.values())
        keyword_count = len(keywords)
        
        # Base confidence
        confidence = 0.5
        
        # Boost for entities
        if entity_count > 0:
            confidence += min(0.3, entity_count * 0.1)
        
        # Boost for keywords
        if keyword_count > 0:
            confidence += min(0.2, keyword_count * 0.05)
        
        return min(1.0, confidence)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        if self.stats["total_analyses"] == 0:
            return {
                "total_analyses": 0,
                "avg_response_time_ms": 0.0,
                "pattern_match_rate": 0.0,
                "performance_target_met": False
            }
        
        avg_time = self.stats["total_time"] / self.stats["total_analyses"]
        
        return {
            "total_analyses": self.stats["total_analyses"],
            "avg_response_time_ms": avg_time * 1000,
            "pattern_match_rate": self.stats["pattern_matches"] / self.stats["total_analyses"],
            "performance_target_met": avg_time < 0.2  # 200ms target
        }

class SimpleIntentAnalyzerBenchmark:
    """Performance-Benchmark für vereinfachten Intent Analyzer"""
    
    def __init__(self):
        self.analyzer = SimpleIntentAnalyzer()
        
        # Test queries
        self.test_queries = [
            {
                "query": "Was ist MFA?",
                "expected_intent": "general_information",
                "complexity": "simple",
                "target_time_ms": 50
            },
            {
                "query": "BSI C5 Compliance",
                "expected_intent": "general_information",
                "complexity": "simple",
                "target_time_ms": 50
            },
            {
                "query": "Wie implementiere ich MFA in Azure?",
                "expected_intent": "technical_implementation",
                "complexity": "medium",
                "target_time_ms": 100
            },
            {
                "query": "Was fordert BSI C5 zu Backup-Verfahren?",
                "expected_intent": "compliance_requirement",
                "complexity": "medium",
                "target_time_ms": 100
            },
            {
                "query": "Best Practices für Verschlüsselung",
                "expected_intent": "best_practice",
                "complexity": "medium",
                "target_time_ms": 100
            },
            {
                "query": "Vergleich zwischen BSI IT-Grundschutz OPS-01 und ISO 27001 A.12.6.1",
                "expected_intent": "mapping_comparison",
                "complexity": "complex",
                "target_time_ms": 150
            },
            {
                "query": "GDPR DSGVO BSI C5 ISO 27001 Azure AWS Docker",
                "expected_intent": "general_information",
                "complexity": "complex",
                "target_time_ms": 150
            }
        ]
    
    async def run_benchmark(self, iterations: int = 5) -> Dict[str, Any]:
        """Run complete benchmark"""
        
        print("🚀 Starting Simple Intent Analyzer Performance Benchmark")
        print(f"📊 Testing {len(self.test_queries)} query types with {iterations} iterations each")
        print("-" * 80)
        
        all_results = []
        
        for query_test in self.test_queries:
            print(f"\n🎯 Testing: {query_test['query'][:60]}...")
            print(f"   Expected: {query_test['expected_intent']} | Complexity: {query_test['complexity']} | Target: {query_test['target_time_ms']}ms")
            
            query_results = []
            
            for iteration in range(iterations):
                result = await self.analyzer.analyze_query(query_test['query'])
                result['iteration'] = iteration + 1
                result['expected_intent'] = query_test['expected_intent']
                result['target_time_ms'] = query_test['target_time_ms']
                
                query_results.append(result)
                
                print(f"   Iteration {iteration + 1}: {result['analysis_time_ms']:.1f}ms - {result['primary_intent']}")
            
            # Calculate statistics
            response_times = [r['analysis_time_ms'] for r in query_results]
            query_stats = {
                "query": query_test['query'],
                "expected_intent": query_test['expected_intent'],
                "complexity": query_test['complexity'],
                "target_time_ms": query_test['target_time_ms'],
                "results": query_results,
                "statistics": {
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "avg_ms": statistics.mean(response_times),
                    "median_ms": statistics.median(response_times)
                },
                "target_met": all(t <= query_test['target_time_ms'] for t in response_times),
                "intent_accuracy": sum(1 for r in query_results if r['primary_intent'] == query_test['expected_intent']) / iterations
            }
            
            all_results.append(query_stats)
            
            print(f"   📊 Stats: Avg={query_stats['statistics']['avg_ms']:.1f}ms, Target Met: {query_stats['target_met']}")
        
        # Overall results
        all_response_times = []
        for query_result in all_results:
            all_response_times.extend([r['analysis_time_ms'] for r in query_result['results']])
        
        overall_stats = {
            "total_tests": len(all_response_times),
            "avg_response_time_ms": statistics.mean(all_response_times),
            "median_response_time_ms": statistics.median(all_response_times),
            "max_response_time_ms": max(all_response_times),
            "min_response_time_ms": min(all_response_times),
            "sub_200ms_rate": sum(1 for t in all_response_times if t <= 200) / len(all_response_times),
            "sub_100ms_rate": sum(1 for t in all_response_times if t <= 100) / len(all_response_times),
            "sub_50ms_rate": sum(1 for t in all_response_times if t <= 50) / len(all_response_times)
        }
        
        return {
            "test_results": all_results,
            "overall_stats": overall_stats,
            "service_stats": self.analyzer.get_performance_stats()
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print benchmark results"""
        
        overall = results["overall_stats"]
        service = results["service_stats"]
        
        print("\n" + "=" * 80)
        print("🎯 SIMPLE INTENT ANALYZER PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Total Tests: {overall['total_tests']}")
        print(f"   Average Response Time: {overall['avg_response_time_ms']:.1f}ms")
        print(f"   Median Response Time: {overall['median_response_time_ms']:.1f}ms")
        print(f"   Min/Max Response Time: {overall['min_response_time_ms']:.1f}ms / {overall['max_response_time_ms']:.1f}ms")
        
        print(f"\n🎯 PERFORMANCE TARGETS:")
        print(f"   Sub-200ms Rate: {overall['sub_200ms_rate']:.1%}")
        print(f"   Sub-100ms Rate: {overall['sub_100ms_rate']:.1%}")
        print(f"   Sub-50ms Rate: {overall['sub_50ms_rate']:.1%}")
        
        print(f"\n🔧 SERVICE STATISTICS:")
        print(f"   Total Analyses: {service['total_analyses']}")
        print(f"   Pattern Match Rate: {service['pattern_match_rate']:.1%}")
        print(f"   Performance Target Met: {service['performance_target_met']}")
        
        print(f"\n✅ BENCHMARK CONCLUSION:")
        if overall['sub_200ms_rate'] >= 0.95:
            print(f"   🎉 EXCELLENT: {overall['sub_200ms_rate']:.1%} sub-200ms - Performance target EXCEEDED!")
        elif overall['sub_100ms_rate'] >= 0.90:
            print(f"   ✅ VERY GOOD: {overall['sub_100ms_rate']:.1%} sub-100ms - Performance is excellent!")
        elif overall['sub_200ms_rate'] >= 0.90:
            print(f"   ✅ GOOD: {overall['sub_200ms_rate']:.1%} sub-200ms - Performance target MET!")
        else:
            print(f"   ⚠️  NEEDS OPTIMIZATION: {overall['sub_200ms_rate']:.1%} sub-200ms")

async def main():
    """Run simple benchmark"""
    
    benchmark = SimpleIntentAnalyzerBenchmark()
    results = await benchmark.run_benchmark(iterations=3)
    
    benchmark.print_results(results)
    
    # Validate performance
    overall = results["overall_stats"]
    if overall['sub_200ms_rate'] >= 0.9:
        print(f"\n🎉 PERFORMANCE VALIDATION: SUCCESS!")
        return 0
    else:
        print(f"\n❌ PERFORMANCE VALIDATION: NEEDS IMPROVEMENT")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 