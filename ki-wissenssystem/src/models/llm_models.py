"""
Pydantic-Modelle für strukturierte LLM-Antworten
Gewährleistet robustes Parsing von LLM-Outputs
"""
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime

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

class QueryIntent(str, Enum):
    """Enum für Query-Intents"""
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    TECHNICAL_IMPLEMENTATION = "technical_implementation"
    MAPPING_COMPARISON = "mapping_comparison"
    BEST_PRACTICE = "best_practice"
    SPECIFIC_CONTROL = "specific_control"
    GENERAL_INFORMATION = "general_information"

class RequestPriorityLevel(str, Enum):
    """Request priority levels for LiteLLM"""
    CRITICAL = "CRITICAL"  # 10 - Intent Analysis
    HIGH = "HIGH"         # 8 - Real-time queries
    MEDIUM = "MEDIUM"     # 6 - Standard processing
    LOW = "LOW"           # 4 - Response synthesis
    BATCH = "BATCH"       # 2 - Background processing

class EntityData(BaseModel):
    """Entity data structure for query analysis"""
    text: str = Field(description="Entity text")
    entity_type: str = Field(description="Type of entity (CONCEPT, STANDARD, TECHNOLOGY, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

class QueryAnalysis(BaseModel):
    """Structured query analysis result"""
    primary_intent: QueryIntent = Field(description="Primary intent of the query")
    secondary_intents: List[QueryIntent] = Field(default_factory=list, description="Secondary intents")
    entities: List[EntityData] = Field(default_factory=list, description="Extracted entities")
    search_keywords: List[str] = Field(default_factory=list, description="Search keywords")
    requires_comparison: bool = Field(default=False, description="Whether query requires comparison")
    temporal_context: Optional[str] = Field(None, description="Temporal context if any")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall analysis confidence")
    complexity_score: float = Field(ge=0.0, le=1.0, description="Query complexity score")

class SynthesizedResponse(BaseModel):
    """Synthesized response from LLM"""
    answer: str = Field(description="Main response text")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references")
    confidence: float = Field(ge=0.0, le=1.0, description="Response confidence")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class LLMRequest(BaseModel):
    """Request structure for LiteLLM client"""
    messages: List[Dict[str, str]] = Field(description="Chat messages")
    model: str = Field(description="Model identifier")
    priority: RequestPriorityLevel = Field(default=RequestPriorityLevel.MEDIUM, description="Request priority")
    purpose: str = Field(description="Purpose/use case for model selection")
    stream: bool = Field(default=False, description="Whether to stream response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature setting")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens")
    timeout: Optional[float] = Field(None, ge=0.1, description="Request timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

class LLMResponse(BaseModel):
    """Response structure from LiteLLM client"""
    content: str = Field(description="Response content")
    model: str = Field(description="Model used")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")
    response_time: float = Field(description="Response time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")

class LLMStreamResponse(BaseModel):
    """Stream response chunk from LiteLLM client"""
    content: str = Field(description="Content chunk")
    model: str = Field(description="Model used")
    finish_reason: Optional[str] = Field(None, description="Reason for completion if finished")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    chunk_index: int = Field(description="Index of this chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")

class LLMMessage(BaseModel):
    """Message structure for LLM conversations"""
    role: str = Field(description="Message role (user, assistant, system)")
    content: str = Field(description="Message content")

class EmbeddingRequest(BaseModel):
    """Request structure for embeddings"""
    input: Union[str, List[str]] = Field(description="Text to embed")
    model: str = Field(description="Embedding model identifier")
    encoding_format: str = Field(default="float", description="Encoding format")
    dimensions: Optional[int] = Field(None, description="Number of dimensions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

class EmbeddingResponse(BaseModel):
    """Response structure for embeddings"""
    embeddings: List[List[float]] = Field(description="Generated embeddings")
    model: str = Field(description="Model used")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")

class ModelCapabilities(BaseModel):
    """Model capabilities and features"""
    model_name: str = Field(description="Model identifier")
    supports_streaming: bool = Field(default=False, description="Whether model supports streaming")
    supports_function_calling: bool = Field(default=False, description="Whether model supports function calling")
    max_tokens: Optional[int] = Field(None, description="Maximum token limit")
    supports_vision: bool = Field(default=False, description="Whether model supports vision/images")
    context_window: Optional[int] = Field(None, description="Context window size")
    cost_per_token: Optional[float] = Field(None, description="Cost per token")

class RequestPriority(BaseModel):
    """Request priority configuration"""
    level: RequestPriorityLevel = Field(description="Priority level")
    queue_position: int = Field(description="Position in priority queue")
    estimated_wait_time: Optional[float] = Field(None, description="Estimated wait time in seconds")

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