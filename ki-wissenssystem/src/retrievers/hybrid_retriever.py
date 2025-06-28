from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from src.retrievers.intent_analyzer import QueryAnalysis, QueryIntent
from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient
from src.config.settings import settings
from src.retrievers.query_expander import QueryExpander, ExpandedQuery
from src.models.llm_models import SmartRetrievalStrategy
import logging

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Container for retrieval results"""
    source: str  # "graph" or "vector"
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    node_type: Optional[str] = None
    relationships: List[Dict[str, Any]] = None

class HybridRetriever:
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.chroma = ChromaClient()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.query_expander = QueryExpander()
    
    async def retrieve(
        self, 
        query: str, 
        analysis: QueryAnalysis,
        max_results: int = 20
    ) -> List[RetrievalResult]:
        """Perform hybrid retrieval based on query analysis"""
        
        # 1. Query Expansion für bessere Abdeckung
        expanded_query = await self.query_expander.expand_query(query)
        logger.info(f"Query expanded: {len(expanded_query.expanded_terms)} additional terms")
        
        # 2. Intelligente Retrieval-Strategie bestimmen
        strategy = await self._determine_smart_strategy(analysis, expanded_query)
        
        # 3. Parallel retrieval mit erweiterten Begriffen
        tasks = []
        
        if strategy.get("use_graph", True):
            tasks.append(self._enhanced_graph_retrieval(
                analysis, expanded_query, strategy.get("graph_config", {})
            ))
        
        if strategy.get("use_vector", True):
            tasks.append(self._enhanced_vector_retrieval(
                query, expanded_query, analysis, strategy.get("vector_config", {})
            ))
        
        # Wait for all retrievals
        results = await asyncio.gather(*tasks)
        
        # Flatten and merge results
        all_results = []
        for result_set in results:
            all_results.extend(result_set)
        
        # Enhanced ranking mit Query-Expansion-Kontext
        ranked_results = self._rank_results_with_expansion(all_results, analysis, expanded_query)
        
        return ranked_results[:max_results]
    
    def _determine_strategy(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Determine retrieval strategy based on query intent"""
        
        strategies = {
            QueryIntent.SPECIFIC_CONTROL: {
                "use_graph": True,
                "use_vector": True,
                "graph_config": {"focus": "control_lookup", "depth": 2},
                "vector_config": {"collections": ["compliance"], "boost_exact": True}
            },
            QueryIntent.COMPLIANCE_REQUIREMENT: {
                "use_graph": True,
                "use_vector": True,
                "graph_config": {"focus": "requirements", "depth": 2},
                "vector_config": {"collections": ["compliance", "technical"]}
            },
            QueryIntent.TECHNICAL_IMPLEMENTATION: {
                "use_graph": True,
                "use_vector": True,
                "graph_config": {"focus": "technologies", "depth": 3},
                "vector_config": {"collections": ["technical", "general"], "boost_technical": True}
            },
            QueryIntent.MAPPING_COMPARISON: {
                "use_graph": True,
                "use_vector": True,
                "graph_config": {"focus": "mappings", "depth": 2},
                "vector_config": {"collections": ["compliance"]}
            },
            QueryIntent.BEST_PRACTICE: {
                "use_graph": False,
                "use_vector": True,
                "graph_config": {},
                "vector_config": {"collections": ["technical", "general"], "boost_recent": True}
            },
            QueryIntent.GENERAL_INFORMATION: {
                "use_graph": False,
                "use_vector": True,
                "graph_config": {},
                "vector_config": {"collections": ["general", "technical"]}
            }
        }
        
        return strategies.get(analysis.primary_intent, strategies[QueryIntent.GENERAL_INFORMATION])

    async def _determine_smart_strategy(self, analysis: QueryAnalysis, expanded_query: ExpandedQuery) -> Dict[str, Any]:
        """Bestimmt intelligente Retrieval-Strategie basierend auf erweiterten Query-Informationen"""
        
        base_strategy = self._determine_strategy(analysis)
        
        # Strategieanpassung basierend auf Query-Expansion
        if len(expanded_query.expanded_terms) > 10:
            # Viele erweiterte Begriffe -> mehr Fokus auf Graph-Traversierung
            base_strategy["graph_config"]["depth"] = min(3, base_strategy["graph_config"].get("depth", 2) + 1)
        
        if any("control" in term.lower() for term in expanded_query.context_terms):
            # Control-Kontext erkannt -> Graph-Gewichtung erhöhen
            base_strategy["use_graph"] = True
            base_strategy["graph_config"]["focus"] = "control_lookup"
        
        if any("technical" in term.lower() for term in expanded_query.context_terms):
            # Technischer Kontext -> Vector-Suche in technischen Collections priorisieren
            base_strategy["vector_config"]["collections"] = ["technical", "compliance"]
        
        return base_strategy

    async def _enhanced_graph_retrieval(
        self, 
        analysis: QueryAnalysis,
        expanded_query: ExpandedQuery,
        config: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """Erweiterte Graph-Retrieval mit Query-Expansion"""
        
        results = []
        
        # Original Graph-Retrieval
        original_results = await self._graph_retrieval(analysis, config)
        results.extend(original_results)
        
        # Zusätzliche Suche mit erweiterten Begriffen
        loop = asyncio.get_event_loop()
        
        for term in expanded_query.expanded_terms[:5]:  # Limit für Performance
            try:
                expanded_results = await loop.run_in_executor(
                    self.executor,
                    self.neo4j.search_controls,
                    term
                )
                
                for node in expanded_results:
                    # Konfidenz basierend auf Query-Expansion-Score anpassen
                    confidence = expanded_query.confidence_scores.get(term, 0.5)
                    
                    results.append(RetrievalResult(
                        source="graph_expanded",
                        content=node.get("text", ""),
                        metadata={**node, "expansion_term": term},
                        relevance_score=0.6 * confidence,  # Leicht reduziert für erweiterte Begriffe
                        node_type="ControlItem"
                    ))
            except Exception as e:
                logger.error(f"Error in expanded graph search for {term}: {e}")
        
        return results

    async def _enhanced_vector_retrieval(
        self,
        original_query: str,
        expanded_query: ExpandedQuery,
        analysis: QueryAnalysis,
        config: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """Erweiterte Vector-Retrieval mit Query-Expansion"""
        
        results = []
        
        # Original Vector-Retrieval
        original_results = await self._vector_retrieval(original_query, analysis, config)
        results.extend(original_results)
        
        # Zusätzliche Suche mit alternativen Formulierungen
        for alternative in expanded_query.alternative_phrasings[:3]:  # Max 3 Alternativen
            try:
                alt_results = await self._vector_retrieval(alternative, analysis, config)
                
                # Markiere als alternative Formulierung und reduziere Score leicht
                for result in alt_results:
                    result.metadata["from_alternative"] = alternative
                    result.relevance_score *= 0.9  # Leichte Reduzierung
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error in alternative query retrieval: {e}")
        
        return results

    def _rank_results_with_expansion(
        self,
        results: List[RetrievalResult],
        analysis: QueryAnalysis,
        expanded_query: ExpandedQuery
    ) -> List[RetrievalResult]:
        """Ranking mit Berücksichtigung der Query-Expansion"""
        
        scored_results = []
        
        for result in results:
            base_score = result.relevance_score
            
            # Bonus für Original-Begriffe vs. erweiterte Begriffe
            content_lower = result.content.lower()
            
            # Bonus für Original-Query-Begriffe
            original_bonus = 0.0
            for keyword in analysis.search_keywords:
                if keyword.lower() in content_lower:
                    original_bonus += 0.2
            
            # Bonus für hochkonfidente erweiterte Begriffe
            expansion_bonus = 0.0
            for term, confidence in expanded_query.confidence_scores.items():
                if term.lower() in content_lower and confidence > 0.7:
                    expansion_bonus += 0.1 * confidence
            
            # Penalty für sehr niedrigkonfidente Erweiterungen
            if hasattr(result, 'metadata') and result.metadata.get("expansion_term"):
                expansion_term = result.metadata["expansion_term"]
                confidence = expanded_query.confidence_scores.get(expansion_term, 0.5)
                if confidence < 0.4:
                    base_score *= 0.8  # 20% Penalty
            
            final_score = base_score + original_bonus + expansion_bonus
            
            result.relevance_score = final_score
            scored_results.append(result)
        
        # Sortieren nach finaler Relevanz
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return scored_results
    
    async def _graph_retrieval(
        self, 
        analysis: QueryAnalysis, 
        config: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """Retrieve from Neo4j knowledge graph"""
        
        loop = asyncio.get_event_loop()
        results = []
        
        focus = config.get("focus", "general")
        depth = config.get("depth", 2)
        
        # Search for specific controls
        if analysis.entities.get("controls"):
            for control_id in analysis.entities["controls"]:
                try:
                    # Direct control lookup
                    control_results = await loop.run_in_executor(
                        self.executor,
                        self._get_control_with_context,
                        control_id,
                        depth
                    )
                    results.extend(control_results)
                except Exception as e:
                    logger.error(f"Error retrieving control {control_id}: {e}")
        
        # Search by keywords in graph
        if analysis.search_keywords and focus != "control_lookup":
            for keyword in analysis.search_keywords[:5]:  # Limit keywords
                try:
                    keyword_results = await loop.run_in_executor(
                        self.executor,
                        self.neo4j.search_controls,
                        keyword
                    )
                    
                    for node in keyword_results:
                        results.append(RetrievalResult(
                            source="graph",
                            content=node.get("text", ""),
                            metadata=node,
                            relevance_score=0.8,
                            node_type="ControlItem"
                        ))
                except Exception as e:
                    logger.error(f"Error searching graph for {keyword}: {e}")
        
        # Technology-based search
        if analysis.entities.get("technologies") and focus == "technologies":
            for tech in analysis.entities["technologies"]:
                try:
                    tech_results = await loop.run_in_executor(
                        self.executor,
                        self._get_technology_implementations,
                        tech
                    )
                    results.extend(tech_results)
                except Exception as e:
                    logger.error(f"Error retrieving technology {tech}: {e}")
        
        # Mapping search for comparison queries
        if focus == "mappings" and len(analysis.entities.get("standards", [])) > 1:
            try:
                mapping_results = await loop.run_in_executor(
                    self.executor,
                    self._get_standard_mappings,
                    analysis.entities["standards"]
                )
                results.extend(mapping_results)
            except Exception as e:
                logger.error(f"Error retrieving mappings: {e}")
        
        return results
    
    def _get_control_with_context(self, control_id: str, depth: int) -> List[RetrievalResult]:
        """Get control and its related nodes"""
        results = []
        
        # Get the control itself
        with self.neo4j.driver.session() as session:
            control_result = session.run("""
                MATCH (c:ControlItem {id: $control_id})
                RETURN c
            """, control_id=control_id)
            
            control_record = control_result.single()
            if control_record:
                control = dict(control_record["c"])
                results.append(RetrievalResult(
                    source="graph",
                    content=control.get("text", ""),
                    metadata=control,
                    relevance_score=1.0,
                    node_type="ControlItem"
                ))
                
                # Get related nodes
                related = self.neo4j.find_related_nodes(control_id, depth)
                for rel_node in related[:10]:  # Limit related nodes
                    node_data = rel_node["node"]
                    results.append(RetrievalResult(
                        source="graph",
                        content=node_data.get("text", node_data.get("summary", "")),
                        metadata=node_data,
                        relevance_score=0.8 / rel_node["distance"],
                        node_type=rel_node["labels"][0] if rel_node["labels"] else None
                    ))
        
        return results
    
    def _get_technology_implementations(self, technology: str) -> List[RetrievalResult]:
        """Get controls implemented by a technology"""
        results = []
        
        with self.neo4j.driver.session() as session:
            result = session.run("""
                MATCH (t:Technology {name: $tech})-[:IMPLEMENTS]->(c:ControlItem)
                RETURN c, t
                LIMIT 20
            """, tech=technology)
            
            for record in result:
                control = dict(record["c"])
                tech = dict(record["t"])
                
                results.append(RetrievalResult(
                    source="graph",
                    content=control.get("text", ""),
                    metadata={**control, "technology": tech},
                    relevance_score=0.9,
                    node_type="ControlItem"
                ))
        
        return results
    
    def _get_standard_mappings(self, standards: List[str]) -> List[RetrievalResult]:
        """Get mappings between standards"""
        results = []
        
        if len(standards) < 2:
            return results
        
        with self.neo4j.driver.session() as session:
            # Query for mappings between standards
            result = session.run("""
                MATCH (c1:ControlItem)-[:MAPS_TO]->(c2:ControlItem)
                WHERE c1.source CONTAINS $std1 AND c2.source CONTAINS $std2
                RETURN c1, c2
                LIMIT 30
            """, std1=standards[0], std2=standards[1])
            
            for record in result:
                c1 = dict(record["c1"])
                c2 = dict(record["c2"])
                
                content = f"Mapping: {c1['id']} ({c1['title']}) ↔ {c2['id']} ({c2['title']})"
                
                results.append(RetrievalResult(
                    source="graph",
                    content=content,
                    metadata={"control1": c1, "control2": c2},
                    relevance_score=0.95,
                    node_type="Mapping"
                ))
        
        return results
    
    async def _vector_retrieval(
        self,
        query: str,
        analysis: QueryAnalysis,
        config: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """Retrieve from ChromaDB vector store"""
        
        loop = asyncio.get_event_loop()
        
        # Prepare search query
        search_query = self._prepare_vector_query(query, analysis)
        
        # Determine collections
        collections = config.get("collections", ["general"])
        
        # Build filter
        metadata_filter = self._build_metadata_filter(analysis, config)
        
        try:
            # Perform vector search
            vector_results = await loop.run_in_executor(
                self.executor,
                self.chroma.search_similar,
                search_query,
                collections,
                30,  # Get more results for ranking
                metadata_filter
            )
            
            # Convert to RetrievalResult
            results = []
            for vr in vector_results:
                # Calculate relevance score (inverse of distance)
                relevance = 1.0 / (1.0 + vr["distance"])
                
                # Boost if exact match
                if config.get("boost_exact") and any(
                    keyword.lower() in vr["text"].lower() 
                    for keyword in analysis.search_keywords
                ):
                    relevance *= 1.2
                
                results.append(RetrievalResult(
                    source="vector",
                    content=vr["text"],
                    metadata=vr["metadata"],
                    relevance_score=min(1.0, relevance),
                    node_type="KnowledgeChunk"
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector retrieval: {e}")
            return []
    
    def _prepare_vector_query(self, query: str, analysis: QueryAnalysis) -> str:
        """Prepare optimized query for vector search"""
        # Combine original query with extracted keywords
        query_parts = [query]
        
        # Add important entities
        if analysis.entities.get("concepts"):
            query_parts.extend(analysis.entities["concepts"])
        
        # Add key technologies if searching for implementation
        if analysis.primary_intent == QueryIntent.TECHNICAL_IMPLEMENTATION:
            query_parts.extend(analysis.entities.get("technologies", []))
        
        return " ".join(query_parts)
    
    def _build_metadata_filter(
        self,
        analysis: QueryAnalysis,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Build metadata filter for vector search"""
        filters = {}
        
        # Filter by source/standard if specific standard mentioned
        if analysis.entities.get("standards"):
            # Use $in operator instead of $contains for ChromaDB compatibility
            standards_list = analysis.entities["standards"]
            filters["source"] = {"$in": standards_list}
        
        # Filter by document type for technical queries
        if config.get("boost_technical"):
            filters["document_type"] = {"$in": ["WHITEPAPER", "TECHNICAL_DOC"]}
        
        return filters if filters else None
    
    def _rank_results(
        self,
        results: List[RetrievalResult],
        analysis: QueryAnalysis
    ) -> List[RetrievalResult]:
        """Rank and deduplicate results"""
        
        # Deduplicate by content similarity
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_key = result.content[:100]  # Use first 100 chars as key
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)
        
        # Calculate final scores
        for result in unique_results:
            score = result.relevance_score
            
            # Boost graph results for specific control queries
            if result.source == "graph" and analysis.primary_intent == QueryIntent.SPECIFIC_CONTROL:
                score *= 1.3
            
            # Boost vector results for implementation queries
            if result.source == "vector" and analysis.primary_intent == QueryIntent.TECHNICAL_IMPLEMENTATION:
                score *= 1.2
            
            # Boost if contains multiple keywords
            keyword_matches = sum(
                1 for keyword in analysis.search_keywords 
                if keyword.lower() in result.content.lower()
            )
            score *= (1 + 0.1 * keyword_matches)
            
            result.relevance_score = min(1.0, score)
        
        # Sort by relevance
        unique_results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return unique_results