"""
Advanced Query Expansion & Context Enrichment
Erweitert Benutzeranfragen um verwandte Begriffe und Kontext
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import re
import logging

from src.config.llm_config import llm_router, ModelPurpose
from src.storage.neo4j_client import Neo4jClient
from src.models.llm_models import QueryExpansion, ConfidenceLevel
from src.utils.llm_parser import LLMParser

logger = logging.getLogger(__name__)

@dataclass
class ExpandedQuery:
    """Erweiterte Query mit Kontext und Synonymen"""
    original_query: str
    expanded_terms: List[str]
    context_terms: List[str]
    confidence_scores: Dict[str, float]
    expansion_reasoning: str
    alternative_phrasings: List[str]

class QueryExpander:
    """Erweitert Queries für bessere Retrieval-Ergebnisse"""
    
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.SYNTHESIS)
        self.neo4j = Neo4jClient()
        self.parser = LLMParser()
        
        # Synonym-Mappings für technische Begriffe
        self.technical_synonyms = {
            "passwort": ["password", "kennwort", "authentifizierung", "login"],
            "server": ["system", "rechner", "maschine", "host"],
            "netzwerk": ["network", "lan", "wan", "infrastruktur"],
            "sicherheit": ["security", "schutz", "absicherung"],
            "backup": ["sicherung", "datensicherung", "archivierung"],
            "encryption": ["verschlüsselung", "chiffrierung", "kryptographie"],
            "firewall": ["brandmauer", "paketfilter", "netzwerkschutz"],
            "active_directory": ["ad", "verzeichnisdienst", "ldap", "domain_controller"],
            "compliance": ["konformität", "regelkonformität", "einhaltung"],
            "audit": ["prüfung", "revision", "kontrolle", "auditierung"]
        }
        
        # Control-ID Pattern Recognition
        self.control_patterns = [
            r'\b([A-Z]{2,4}\.?\d+\.?A\d+)\b',  # BSI Format: ORP.4.A1
            r'\b([A-Z]{2,4}-\d+)\b',           # ISO Format: AC-2
            r'\b([A-Z]{3}\.\d{2})\b'           # Alternative: SYS.01
        ]

    async def expand_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> ExpandedQuery:
        """Hauptmethode für Query Expansion"""
        
        logger.info(f"Expanding query: {query[:50]}...")
        
        # 1. Basis-Analyse
        original_terms = self._extract_terms(query)
        control_ids = self._extract_control_ids(query)
        
        # 2. Technische Synonyme hinzufügen
        technical_synonyms = self._get_technical_synonyms(original_terms)
        
        # 3. Graph-basierte Kontext-Terme
        graph_context = await self._get_graph_context(original_terms + control_ids)
        
        # 4. LLM-basierte Expansion
        llm_expansion = await self._llm_expand_query(query, context)
        
        # 5. Alternative Formulierungen
        alternatives = await self._generate_alternatives(query)
        
        # 6. Ergebnisse kombinieren und bewerten
        expanded_terms = list(set(
            original_terms + 
            technical_synonyms + 
            graph_context.get('related_terms', []) +
            llm_expansion.expanded_terms
        ))
        
        context_terms = list(set(
            graph_context.get('context_terms', []) +
            llm_expansion.context_terms
        ))
        
        # Konfidenz-Scores berechnen
        confidence_scores = self._calculate_confidence_scores(
            original_terms, expanded_terms, llm_expansion
        )
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=expanded_terms,
            context_terms=context_terms,
            confidence_scores=confidence_scores,
            expansion_reasoning=llm_expansion.reasoning,
            alternative_phrasings=alternatives
        )

    def _extract_terms(self, query: str) -> List[str]:
        """Extrahiert relevante Terme aus der Query"""
        
        # Grundlegende Term-Extraktion
        terms = []
        
        # Entferne Stopwörter und extrahiere wichtige Begriffe
        stopwords = {'der', 'die', 'das', 'und', 'oder', 'ist', 'sind', 'ein', 'eine', 'wie', 'was', 'wo', 'wann', 'warum'}
        
        # Wörter extrahieren (mindestens 3 Zeichen)
        words = re.findall(r'\b\w{3,}\b', query.lower())
        terms = [word for word in words if word not in stopwords]
        
        # Phrasen erkennen (zusammengesetzte Begriffe)
        phrases = re.findall(r'\b\w+[-_]\w+\b', query.lower())
        terms.extend(phrases)
        
        return list(set(terms))

    def _extract_control_ids(self, query: str) -> List[str]:
        """Extrahiert Control-IDs aus der Query"""
        
        control_ids = []
        
        for pattern in self.control_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            control_ids.extend(matches)
        
        return list(set(control_ids))

    def _get_technical_synonyms(self, terms: List[str]) -> List[str]:
        """Fügt technische Synonyme hinzu"""
        
        synonyms = []
        
        for term in terms:
            term_lower = term.lower()
            
            # Direkte Synonyme
            if term_lower in self.technical_synonyms:
                synonyms.extend(self.technical_synonyms[term_lower])
            
            # Partielle Matches für zusammengesetzte Begriffe
            for key, values in self.technical_synonyms.items():
                if term_lower in key or key in term_lower:
                    synonyms.extend(values)
        
        return list(set(synonyms))

    async def _get_graph_context(self, terms: List[str]) -> Dict[str, List[str]]:
        """Holt verwandte Begriffe aus dem Knowledge Graph"""
        
        if not terms:
            return {'related_terms': [], 'context_terms': []}
        
        # Cypher-Query für verwandte Begriffe
        cypher_query = """
        UNWIND $terms as term
        MATCH (n)
        WHERE toLower(n.title) CONTAINS toLower(term) 
           OR toLower(n.name) CONTAINS toLower(term)
           OR toLower(n.id) CONTAINS toLower(term)
        
        // Hole direkt verwandte Knoten
        OPTIONAL MATCH (n)-[r]-(related)
        WHERE type(r) IN ['IMPLEMENTS', 'SUPPORTS', 'REFERENCES', 'RELATES_TO']
        
        // Hole auch Knoten im gleichen Bereich/Domain
        OPTIONAL MATCH (n)-[:BELONGS_TO]->(domain)<-[:BELONGS_TO]-(domain_related)
        
        RETURN 
            collect(DISTINCT n.title) as direct_matches,
            collect(DISTINCT related.title) as related_terms,
            collect(DISTINCT domain_related.title) as context_terms,
            collect(DISTINCT n.domain) as domains
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(cypher_query, terms=terms)
                record = result.single()
                
                if record:
                    return {
                        'related_terms': [t for t in record['related_terms'] if t],
                        'context_terms': [t for t in record['context_terms'] if t],
                        'domains': [d for d in record['domains'] if d]
                    }
        
        except Exception as e:
            logger.warning(f"Graph context lookup failed: {e}")
        
        return {'related_terms': [], 'context_terms': []}

    async def _llm_expand_query(self, query: str, context: Optional[Dict[str, Any]]) -> QueryExpansion:
        """LLM-basierte Query-Expansion"""
        
        prompt = f"""Erweitere die folgende Suchanfrage um verwandte Begriffe und Konzepte:

ANFRAGE: "{query}"

KONTEXT:
{context or "Keine zusätzlichen Kontextinformationen verfügbar"}

Analysiere die Anfrage und:
1. Identifiziere verwandte technische Begriffe
2. Erkenne implizite Konzepte
3. Füge relevante Synonyme hinzu
4. Berücksichtige Compliance- und Sicherheitskontext

Antworte im JSON-Format:
{{
    "expanded_terms": ["begriff1", "begriff2", ...],
    "context_terms": ["kontext1", "kontext2", ...],
    "reasoning": "Begründung für die Erweiterung",
    "confidence": "HIGH/MEDIUM/LOW",
    "implicit_concepts": ["konzept1", "konzept2", ...]
}}"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            
            # Parse mit robustem Parser
            expansion = self.parser.parse_llm_response(
                response.content,
                QueryExpansion,
                fallback_values={
                    "expanded_terms": [],
                    "context_terms": [],
                    "reasoning": "LLM parsing failed",
                    "confidence": ConfidenceLevel.LOW,
                    "implicit_concepts": []
                }
            )
            
            return expansion
            
        except Exception as e:
            logger.error(f"LLM query expansion failed: {e}")
            
            # Fallback-Expansion
            return QueryExpansion(
                expanded_terms=[],
                context_terms=[],
                reasoning=f"LLM expansion failed: {str(e)}",
                confidence=ConfidenceLevel.LOW,
                implicit_concepts=[]
            )

    async def _generate_alternatives(self, query: str) -> List[str]:
        """Generiert alternative Formulierungen der Query"""
        
        prompt = f"""Generiere 3-5 alternative Formulierungen für diese Suchanfrage:

ORIGINAL: "{query}"

Die Alternativen sollen:
- Dieselbe Intention haben
- Verschiedene Begriffe/Synonyme verwenden
- Verschiedene Fragestrukturen nutzen
- Im IT-Security/Compliance-Kontext relevant sein

Antworte nur mit den alternativen Formulierungen, eine pro Zeile."""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            
            alternatives = [
                line.strip().strip('"').strip("'") 
                for line in response.content.split('\n') 
                if line.strip() and line.strip() != query
            ]
            
            return alternatives[:5]  # Max 5 Alternativen
            
        except Exception as e:
            logger.error(f"Alternative generation failed: {e}")
            return []

    def _calculate_confidence_scores(
        self, 
        original_terms: List[str], 
        expanded_terms: List[str], 
        llm_expansion: QueryExpansion
    ) -> Dict[str, float]:
        """Berechnet Konfidenz-Scores für erweiterte Begriffe"""
        
        confidence_map = {
            ConfidenceLevel.HIGH: 0.9,
            ConfidenceLevel.MEDIUM: 0.7,
            ConfidenceLevel.LOW: 0.4
        }
        
        base_confidence = confidence_map.get(llm_expansion.confidence, 0.5)
        
        scores = {}
        
        for term in expanded_terms:
            if term in original_terms:
                scores[term] = 1.0  # Originale Begriffe haben höchste Konfidenz
            elif term in self._get_all_synonyms():
                scores[term] = 0.8  # Bekannte Synonyme
            elif term in llm_expansion.expanded_terms:
                scores[term] = base_confidence  # LLM-Vorschläge
            else:
                scores[term] = 0.6  # Graph-basierte Erweiterungen
        
        return scores

    def _get_all_synonyms(self) -> Set[str]:
        """Gibt alle bekannten Synonyme zurück"""
        all_synonyms = set()
        for synonyms in self.technical_synonyms.values():
            all_synonyms.update(synonyms)
        return all_synonyms

    async def get_expansion_suggestions(self, partial_query: str) -> List[str]:
        """Liefert Echtzeit-Vorschläge während der Eingabe"""
        
        if len(partial_query) < 3:
            return []
        
        # Graph-basierte Vorschläge
        cypher_query = """
        MATCH (n)
        WHERE toLower(n.title) CONTAINS toLower($partial)
           OR toLower(n.name) CONTAINS toLower($partial)
        RETURN DISTINCT n.title as suggestion
        ORDER BY length(n.title)
        LIMIT 10
        """
        
        suggestions = []
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(cypher_query, partial=partial_query)
                suggestions = [record['suggestion'] for record in result if record['suggestion']]
        
        except Exception as e:
            logger.warning(f"Suggestion lookup failed: {e}")
        
        # Ergänze um Synonym-Vorschläge
        for key, values in self.technical_synonyms.items():
            if partial_query.lower() in key:
                suggestions.extend(values)
        
        return list(set(suggestions))[:10] 