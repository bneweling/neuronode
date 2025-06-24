from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.config.llm_config import llm_router, ModelPurpose
import re
import logging

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    COMPLIANCE_REQUIREMENT = "compliance_requirement"  # "Was fordert BSI C5 zu MFA?"
    TECHNICAL_IMPLEMENTATION = "technical_implementation"  # "Wie implementiere ich MFA in Azure?"
    MAPPING_COMPARISON = "mapping_comparison"  # "Wie verhält sich BSI zu ISO 27001?"
    BEST_PRACTICE = "best_practice"  # "Was sind Best Practices für..."
    SPECIFIC_CONTROL = "specific_control"  # "Was sagt OPS-01?"
    GENERAL_INFORMATION = "general_information"  # "Was ist Zero Trust?"

class QueryAnalysis(BaseModel):
    """Structured analysis of a user query"""
    primary_intent: QueryIntent = Field(description="Primary intent of the query")
    secondary_intents: List[QueryIntent] = Field(default_factory=list, description="Additional intents")
    entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Extracted entities by type (standards, technologies, controls, concepts)"
    )
    search_keywords: List[str] = Field(description="Key terms for search")
    requires_comparison: bool = Field(default=False, description="Whether query requires comparing standards")
    temporal_context: Optional[str] = Field(default=None, description="Time context if any")
    confidence: float = Field(description="Confidence in analysis (0-1)")

class IntentAnalyzer:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.EXTRACTION)
        self.parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        
        # Known entity patterns
        self.patterns = {
            "bsi_control": re.compile(r'\b([A-Z]{3,4}[-.]?\d+(?:\.\d+)*(?:\.A\d+)?)\b'),
            "c5_control": re.compile(r'\b([A-Z]{2,3}-\d{2})\b'),
            "iso_control": re.compile(r'\b(?:ISO\s*)?(?:27001|27002)(?:\s*[:\-]\s*)?([A-Z]?\d+(?:\.\d+)*)\b', re.I),
            "technology": re.compile(r'\b(Azure|AWS|GCP|Active Directory|Entra|Office 365|SharePoint|Teams)\b', re.I),
            "standard": re.compile(r'\b(BSI(?:\s+(?:C5|IT-Grundschutz))?|ISO\s*2700[0-9]|NIST(?:\s+CSF)?|SOC\s*2)\b', re.I)
        }
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Experte für die Analyse von Compliance- und Sicherheitsfragen.
            
            Analysiere die Nutzeranfrage und identifiziere:
            
            1. **Primary Intent** - Was will der Nutzer hauptsächlich wissen?
               - compliance_requirement: Anforderungen eines Standards
               - technical_implementation: Technische Umsetzung
               - mapping_comparison: Vergleich zwischen Standards
               - best_practice: Best Practices und Empfehlungen
               - specific_control: Spezifische Control-Abfrage
               - general_information: Allgemeine Informationen
            
            2. **Entities** - Extrahiere alle relevanten Entitäten:
               - standards: Compliance-Standards (BSI C5, ISO 27001, etc.)
               - technologies: Technologien/Produkte (Azure, AWS, etc.)
               - controls: Spezifische Control-IDs
               - concepts: Sicherheitskonzepte (MFA, Encryption, etc.)
            
            3. **Search Keywords** - Wichtige Suchbegriffe
            
            4. **Special Requirements**:
               - requires_comparison: Müssen Standards verglichen werden?
               - temporal_context: Gibt es zeitliche Einschränkungen?
            
            {format_instructions}"""),
            ("human", "Anfrage: {query}")
        ])
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze user query to understand intent and extract entities"""
        
        # First, do pattern-based extraction
        extracted_entities = self._extract_entities_with_patterns(query)
        
        # Then use LLM for deeper analysis
        chain = self.analysis_prompt | self.llm | self.parser
        
        try:
            analysis = await chain.ainvoke({
                "query": query,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Merge pattern-based and LLM-based entities
            for entity_type, entities in extracted_entities.items():
                if entity_type in analysis.entities:
                    # Combine and deduplicate
                    analysis.entities[entity_type] = list(set(
                        analysis.entities[entity_type] + entities
                    ))
                else:
                    analysis.entities[entity_type] = entities
            
            # Adjust confidence based on entity extraction
            if extracted_entities:
                analysis.confidence = min(1.0, analysis.confidence + 0.1)
            
            logger.info(f"Query analysis: Intent={analysis.primary_intent.value}, "
                       f"Entities={len(analysis.entities)}, Confidence={analysis.confidence}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Fallback to basic analysis
            return self._fallback_analysis(query, extracted_entities)
    
    def _extract_entities_with_patterns(self, query: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        entities = {
            "controls": [],
            "technologies": [],
            "standards": []
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
        
        # Clean up and deduplicate
        for key in entities:
            entities[key] = list(set(filter(None, entities[key])))
        
        return entities
    
    def _fallback_analysis(self, query: str, entities: Dict[str, List[str]]) -> QueryAnalysis:
        """Fallback analysis when LLM fails"""
        # Simple keyword-based intent detection
        query_lower = query.lower()
        
        intent = QueryIntent.GENERAL_INFORMATION
        if any(word in query_lower for word in ["was fordert", "anforderung", "muss ich", "compliance"]):
            intent = QueryIntent.COMPLIANCE_REQUIREMENT
        elif any(word in query_lower for word in ["wie implementiere", "umsetzen", "konfigurieren", "einrichten"]):
            intent = QueryIntent.TECHNICAL_IMPLEMENTATION
        elif any(word in query_lower for word in ["vergleich", "unterschied", "mapping", "vs", "versus"]):
            intent = QueryIntent.MAPPING_COMPARISON
        elif any(word in query_lower for word in ["best practice", "empfehlung", "tipps"]):
            intent = QueryIntent.BEST_PRACTICE
        elif entities.get("controls"):
            intent = QueryIntent.SPECIFIC_CONTROL
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        return QueryAnalysis(
            primary_intent=intent,
            secondary_intents=[],
            entities=entities,
            search_keywords=keywords,
            requires_comparison=intent == QueryIntent.MAPPING_COMPARISON,
            confidence=0.6
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common words
        stopwords = {
            "der", "die", "das", "und", "oder", "aber", "mit", "von", "zu", "in",
            "für", "auf", "bei", "nach", "wie", "was", "wann", "wo", "ist", "sind",
            "wird", "werden", "kann", "können", "muss", "müssen", "soll", "sollen"
        }
        
        words = query.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        
        return keywords[:10]  # Limit to top 10
    
    def enhance_query_with_synonyms(self, analysis: QueryAnalysis) -> QueryAnalysis:
        """Enhance query analysis with synonyms and related terms"""
        synonym_map = {
            "mfa": ["multi-factor authentication", "zwei-faktor", "2fa", "mehrstufige authentifizierung"],
            "encryption": ["verschlüsselung", "crypto", "kryptografie"],
            "backup": ["datensicherung", "sicherung", "recovery"],
            "firewall": ["fw", "netzwerk-sicherheit", "perimeter"],
            "identity": ["identität", "iam", "identity management", "identitätsverwaltung"],
            "azure": ["microsoft azure", "azure cloud", "ms azure"],
            "aws": ["amazon web services", "amazon cloud"],
            "patch": ["update", "patching", "aktualisierung", "security update"]
        }
        
        enhanced_keywords = list(analysis.search_keywords)
        
        for keyword in analysis.search_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in synonym_map:
                enhanced_keywords.extend(synonym_map[keyword_lower])
            
            # Also check if keyword is a synonym
            for main_term, synonyms in synonym_map.items():
                if keyword_lower in synonyms:
                    enhanced_keywords.append(main_term)
        
        analysis.search_keywords = list(set(enhanced_keywords))
        return analysis