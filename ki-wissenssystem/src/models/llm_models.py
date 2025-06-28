"""
Pydantic-Modelle für strukturierte LLM-Antworten
Gewährleistet robustes Parsing von LLM-Outputs
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum

class RelationshipType(str, Enum):
    """Enum für Beziehungstypen"""
    IMPLEMENTS = "IMPLEMENTS"
    SUPPORTS = "SUPPORTS"
    REFERENCES = "REFERENCES"
    CONFLICTS = "CONFLICTS"
    NONE = "NONE"

class ConfidenceLevel(str, Enum):
    """Enum für Konfidenz-Level"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class RelationshipAnalysis(BaseModel):
    """Strukturierte LLM-Antwort für Beziehungsanalyse"""
    relationship_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0, description="Konfidenz zwischen 0.0 und 1.0")
    confidence_level: ConfidenceLevel
    context: str = Field(min_length=10, description="Kontext der Beziehung")
    evidence: str = Field(min_length=5, description="Textuelle Evidenz")
    reasoning: str = Field(min_length=10, description="Begründung der Analyse")
    
    @validator('confidence_level', pre=True, always=True)
    def derive_confidence_level(cls, v, values):
        """Leitet Konfidenz-Level aus numerischer Konfidenz ab"""
        if 'confidence' in values:
            conf = values['confidence']
            if conf >= 0.9:
                return ConfidenceLevel.VERY_HIGH
            elif conf >= 0.7:
                return ConfidenceLevel.HIGH
            elif conf >= 0.5:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
        return v

class AmbiguityCheck(BaseModel):
    """Strukturierte LLM-Antwort für Ambiguitätsprüfung"""
    needs_clarification: bool
    confidence: float = Field(ge=0.0, le=1.0)
    prompt: Optional[str] = Field(None, description="Rückfrage an den Nutzer")
    ambiguous_terms: List[str] = Field(default_factory=list)
    reasoning: str = Field(min_length=10, description="Begründung der Einschätzung")
    
    @validator('prompt')
    def prompt_required_if_clarification_needed(cls, v, values):
        """Prompt ist erforderlich wenn Klärung benötigt wird"""
        if values.get('needs_clarification') and not v:
            raise ValueError("Prompt ist erforderlich wenn needs_clarification=True")
        return v

class EntityExtraction(BaseModel):
    """Strukturierte Entitätsextraktion"""
    technologies: List[str] = Field(default_factory=list)
    control_ids: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('technologies', 'control_ids', 'concepts', pre=True)
    def clean_entity_lists(cls, v):
        """Bereinigt Listen von leeren Strings"""
        if isinstance(v, list):
            return [item.strip() for item in v if item and item.strip()]
        return v

class ContextualImplementation(BaseModel):
    """Kontextuelle Implementierung für Graph Gardener"""
    source_id: str
    target_id: str
    relationship_analysis: RelationshipAnalysis
    created_at: Optional[str] = None
    verified: bool = False
    
    class Config:
        use_enum_values = True

class QueryExpansion(BaseModel):
    """Strukturierte LLM-Antwort für Query-Expansion"""
    expanded_terms: List[str] = Field(description="Erweiterte Suchbegriffe")
    context_terms: List[str] = Field(description="Kontextuelle Begriffe")
    reasoning: str = Field(description="Begründung für die Erweiterung")
    confidence: ConfidenceLevel = Field(description="Konfidenz der Expansion")
    implicit_concepts: List[str] = Field(default_factory=list, description="Implizite Konzepte")

class AutoRelationshipCandidate(BaseModel):
    """Kandidat für automatische Beziehungserfassung"""
    source_entity: str = Field(description="Quell-Entität")
    target_entity: str = Field(description="Ziel-Entität")
    relationship_type: RelationshipType = Field(description="Typ der Beziehung")
    confidence: float = Field(ge=0.0, le=1.0, description="Konfidenz der Beziehung")
    evidence: str = Field(description="Textuelle Evidenz")
    source_text: str = Field(description="Ursprungstext")

class SmartRetrievalStrategy(BaseModel):
    """Intelligente Retrieval-Strategie"""
    strategy_type: Literal["semantic", "graph", "hybrid", "keyword"] = Field(description="Strategie-Typ")
    weight: float = Field(ge=0.0, le=1.0, description="Gewichtung der Strategie")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategie-Parameter")
    reasoning: str = Field(description="Begründung für die Strategiewahl") 