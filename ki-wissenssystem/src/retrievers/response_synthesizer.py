from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from src.retrievers.hybrid_retriever import RetrievalResult
from src.retrievers.intent_analyzer import QueryAnalysis, QueryIntent
from src.config.llm_config import llm_router, ModelPurpose
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
import logging

logger = logging.getLogger(__name__)

@dataclass
class SynthesizedResponse:
    """Container for synthesized response"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]
    follow_up_questions: List[str] = None

class ResponseSynthesizer:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.SYNTHESIS)
        
        # Intent-specific prompts
        self.synthesis_prompts = {
            QueryIntent.COMPLIANCE_REQUIREMENT: self._create_compliance_prompt(),
            QueryIntent.TECHNICAL_IMPLEMENTATION: self._create_technical_prompt(),
            QueryIntent.MAPPING_COMPARISON: self._create_mapping_prompt(),
            QueryIntent.BEST_PRACTICE: self._create_best_practice_prompt(),
            QueryIntent.SPECIFIC_CONTROL: self._create_control_prompt(),
            QueryIntent.GENERAL_INFORMATION: self._create_general_prompt()
        }
        
        self.fallback_prompt = self._create_fallback_prompt()
    
    async def synthesize_response(
        self,
        query: str,
        analysis: QueryAnalysis,
        retrieval_results: List[RetrievalResult]
    ) -> SynthesizedResponse:
        """Synthesize a comprehensive response from retrieval results"""
        
        if not retrieval_results:
            return self._create_no_results_response(query, analysis)
        
        # Prepare context
        context = self._prepare_context(retrieval_results, analysis)
        
        # Select appropriate prompt
        prompt = self.synthesis_prompts.get(
            analysis.primary_intent,
            self.fallback_prompt
        )
        
        try:
            # Generate response
            response = await self._generate_response(
                prompt, query, context, analysis
            )
            
            # Extract sources
            sources = self._extract_sources(retrieval_results)
            
            # Generate follow-up questions
            follow_ups = await self._generate_follow_up_questions(
                query, response, analysis
            )
            
            return SynthesizedResponse(
                answer=response,
                sources=sources,
                confidence=self._calculate_confidence(analysis, retrieval_results),
                metadata={
                    "intent": analysis.primary_intent.value,
                    "entities": analysis.entities,
                    "num_sources": len(sources)
                },
                follow_up_questions=follow_ups
            )
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {e}")
            return self._create_error_response(query, str(e))
    
    def _create_compliance_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Compliance-Experte, der Beratern hilft, Anforderungen zu verstehen.
            
            Basierend auf den gefundenen Informationen:
            1. Erkläre die relevanten Compliance-Anforderungen klar und präzise
            2. Nenne die spezifischen Control-IDs und deren Anforderungen
            3. Erwähne das Level/die Kritikalität (falls vorhanden)
            4. Erkläre den Kontext und Zweck der Anforderung
            5. Weise auf verwandte Anforderungen hin
            
            Struktur:
            - Hauptanforderung(en)
            - Details und Kontext
            - Verwandte Controls
            - Praktische Hinweise
            
            Verwende Markdown-Formatierung."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}
            
            Entities: {entities}""")
        ])
    
    def _create_technical_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein technischer Experte, der bei der Implementierung von Sicherheitsmaßnahmen hilft.
            
            Basierend auf den gefundenen Informationen:
            1. Beschreibe konkrete Implementierungsschritte
            2. Nenne spezifische Konfigurationen oder Settings
            3. Erwähne relevante Tools oder Features
            4. Gib Best Practices und Empfehlungen
            5. Weise auf häufige Fehler oder Fallstricke hin
            
            Struktur:
            - Übersicht der Lösung
            - Schritt-für-Schritt Anleitung
            - Technische Details
            - Hinweise und Empfehlungen
            
            Nutze Code-Blöcke für Befehle oder Konfigurationen."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}
            
            Technologien: {technologies}""")
        ])
    
    def _create_mapping_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für Compliance-Mappings zwischen verschiedenen Standards.
            
            Basierend auf den gefundenen Mappings:
            1. Zeige die Entsprechungen zwischen den Standards
            2. Erkläre Gemeinsamkeiten und Unterschiede
            3. Weise auf Lücken oder zusätzliche Anforderungen hin
            4. Gib Empfehlungen für die praktische Umsetzung
            
            Struktur:
            - Mapping-Übersicht (Tabelle wenn möglich)
            - Detaillierte Entsprechungen
            - Unterschiede und Lücken
            - Empfehlungen
            
            Verwende Tabellen für bessere Übersichtlichkeit."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}
            
            Standards: {standards}""")
        ])
    
    def _create_best_practice_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Sicherheitsexperte, der Best Practices empfiehlt.
            
            Basierend auf den gefundenen Informationen:
            1. Stelle bewährte Verfahren vor
            2. Begründe die Empfehlungen
            3. Gib konkrete Beispiele
            4. Erwähne häufige Fehler
            5. Priorisiere die Maßnahmen
            
            Struktur:
            - Top-Empfehlungen
            - Detaillierte Best Practices
            - Umsetzungshinweise
            - Zu vermeidende Fehler
            
            Nutze Aufzählungen und Priorisierungen."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}""")
        ])
    
    def _create_control_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Compliance-Experte, der spezifische Controls erklärt.
            
            Für das/die angefragte(n) Control(s):
            1. Gib die vollständige Control-Beschreibung
            2. Erkläre den Zweck und Kontext
            3. Nenne konkrete Umsetzungsanforderungen
            4. Verweise auf verwandte Controls
            5. Gib Implementierungshinweise
            
            Struktur:
            - Control-Details (ID, Titel, Level)
            - Vollständige Anforderung
            - Erklärung und Kontext
            - Verwandte Controls
            - Umsetzungshinweise"""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}
            
            Control IDs: {control_ids}""")
        ])
    
    def _create_general_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein hilfreicher IT-Sicherheitsexperte.
            
            Beantworte die Frage basierend auf den gefundenen Informationen:
            1. Gib eine klare und verständliche Antwort
            2. Strukturiere die Information logisch
            3. Verwende Beispiele wo hilfreich
            4. Verweise auf relevante Standards oder Best Practices
            
            Sei präzise aber vollständig."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}""")
        ])
    
    def _create_fallback_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein IT-Sicherheitsexperte. 
            Beantworte die Frage basierend auf den verfügbaren Informationen.
            Sei hilfreich und strukturiert."""),
            ("human", """Frage: {query}
            
            Kontext:
            {context}""")
        ])
    
    def _prepare_context(
        self,
        results: List[RetrievalResult],
        analysis: QueryAnalysis
    ) -> str:
        """Prepare context from retrieval results"""
        
        # Group results by type
        grouped = {
            "controls": [],
            "chunks": [],
            "mappings": [],
            "technologies": []
        }
        
        for result in results[:15]:  # Limit context size
            if result.node_type == "ControlItem":
                grouped["controls"].append(result)
            elif result.node_type == "Mapping":
                grouped["mappings"].append(result)
            elif result.metadata.get("technology"):
                grouped["technologies"].append(result)
            else:
                grouped["chunks"].append(result)
        
        # Build context string
        context_parts = []
        
        # Add controls
        if grouped["controls"]:
            context_parts.append("## Relevante Controls:\n")
            for r in grouped["controls"]:
                meta = r.metadata
                context_parts.append(
                    f"**{meta.get('id', 'N/A')} - {meta.get('title', 'N/A')}**\n"
                    f"Level: {meta.get('level', 'N/A')} | Quelle: {meta.get('source', 'N/A')}\n"
                    f"{r.content}\n"
                )
        
        # Add mappings
        if grouped["mappings"]:
            context_parts.append("\n## Mappings:\n")
            for r in grouped["mappings"]:
                context_parts.append(f"{r.content}\n")
        
        # Add general chunks
        if grouped["chunks"]:
            context_parts.append("\n## Weitere Informationen:\n")
            for r in grouped["chunks"]:
                context_parts.append(
                    f"Quelle: {r.metadata.get('source', 'Unknown')}\n"
                    f"{r.content}\n---\n"
                )
        
        return "\n".join(context_parts)
    
    async def _generate_response(
        self,
        prompt: ChatPromptTemplate,
        query: str,
        context: str,
        analysis: QueryAnalysis
    ) -> str:
        """Generate response using LLM"""
        
        # Prepare prompt variables
        prompt_vars = {
            "query": query,
            "context": context,
            "entities": json.dumps(analysis.entities, ensure_ascii=False),
            "technologies": ", ".join(analysis.entities.get("technologies", [])),
            "standards": ", ".join(analysis.entities.get("standards", [])),
            "control_ids": ", ".join(analysis.entities.get("controls", []))
        }
        
        # Filter prompt variables based on what the prompt expects
        messages = prompt.format_messages(**{
            k: v for k, v in prompt_vars.items() 
            if k in prompt.input_variables
        })
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        
        return response.content
    
    def _extract_sources(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Extract and format sources"""
        sources = []
        seen_sources = set()
        
        for result in results[:10]:  # Limit sources
            source_key = f"{result.metadata.get('source', 'unknown')}_{result.metadata.get('id', '')}"
            
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                
                source_info = {
                    "type": result.node_type or "Unknown",
                    "source": result.metadata.get("source", "Unknown"),
                    "relevance": round(result.relevance_score, 2)
                }
                
                # Add specific fields based on type
                if result.node_type == "ControlItem":
                    source_info.update({
                        "control_id": result.metadata.get("id"),
                        "title": result.metadata.get("title")
                    })
                elif result.node_type == "KnowledgeChunk":
                    source_info.update({
                        "summary": result.metadata.get("summary", "")[:100],
                        "page": result.metadata.get("page")
                    })
                
                sources.append(source_info)
        
        return sources
    
    async def _generate_follow_up_questions(
        self,
        query: str,
        response: str,
        analysis: QueryAnalysis
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        
        follow_up_prompt = ChatPromptTemplate.from_messages([
            ("human", """Basierend auf der Frage und Antwort, 
            generiere 3 relevante Folgefragen, die der Nutzer stellen könnte.
            
            Die Fragen sollten:
            - Spezifischer oder tiefer ins Thema gehen
            - Verwandte Aspekte abdecken
            - Praktische nächste Schritte adressieren
            
            Gib nur die Fragen zurück, eine pro Zeile."""),
            ("human", """Ursprüngliche Frage: {query}
            
            Gegebene Antwort (Zusammenfassung): {response_summary}
            
            Intent: {intent}""")
        ])
        
        try:
            # Summarize response if too long
            response_summary = response[:500] + "..." if len(response) > 500 else response
            
            messages = follow_up_prompt.format_messages(
                query=query,
                response_summary=response_summary,
                intent=analysis.primary_intent.value
            )
            
            result = await self.llm.ainvoke(messages)
            
            # Parse questions
            questions = [q.strip() for q in result.content.strip().split("\n") if q.strip()]
            
            return questions[:3]  # Ensure max 3 questions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return []
    
    def _calculate_confidence(
        self,
        analysis: QueryAnalysis,
        results: List[RetrievalResult]
    ) -> float:
        """Calculate confidence score for the response"""
        
        # Base confidence from analysis
        confidence = analysis.confidence
        
        # Adjust based on retrieval results
        if not results:
            return 0.2
        
        # Average relevance of top results
        top_relevance = sum(r.relevance_score for r in results[:5]) / min(5, len(results))
        
        # Adjust based on result diversity
        source_types = set(r.source for r in results[:10])
        if len(source_types) > 1:
            confidence += 0.1  # Boost for diverse sources
        
        # Final confidence
        return min(1.0, (confidence + top_relevance) / 2)
    
    def _create_no_results_response(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> SynthesizedResponse:
        """Create response when no results found"""
        
        answer = f"""Leider konnte ich keine spezifischen Informationen zu Ihrer Anfrage "{query}" finden.

Dies könnte folgende Gründe haben:
- Die Anfrage ist sehr spezifisch und nicht direkt in unserer Wissensbasis abgedeckt
- Die verwendeten Begriffe weichen von den in den Standards verwendeten ab
- Die Information ist möglicherweise in einem noch nicht verarbeiteten Dokument

**Vorschläge:**
- Versuchen Sie es mit alternativen Begriffen oder einer allgemeineren Formulierung
- Prüfen Sie, ob die Control-ID korrekt geschrieben ist
- Fragen Sie nach verwandten Themen oder übergeordneten Konzepten

**Erkannte Elemente in Ihrer Anfrage:**
"""
        
        if analysis.entities:
            for entity_type, entities in analysis.entities.items():
                if entities:
                    answer += f"- {entity_type}: {', '.join(entities)}\n"
        
        return SynthesizedResponse(
            answer=answer,
            sources=[],
            confidence=0.2,
            metadata={"no_results": True, "intent": analysis.primary_intent.value}
        )
    
    def _create_error_response(self, query: str, error: str) -> SynthesizedResponse:
        """Create error response"""
        
        answer = f"""Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten.

**Ihre Frage:** {query}

Bitte versuchen Sie es erneut oder formulieren Sie Ihre Frage um. 
Falls das Problem weiterhin besteht, wenden Sie sich bitte an den Support.

**Technische Details:** {error[:200]}"""
        
        return SynthesizedResponse(
            answer=answer,
            sources=[],
            confidence=0.0,
            metadata={"error": True, "error_message": error}
        )