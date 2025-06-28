#!/usr/bin/env python3
"""
Golden Set Generator from Knowledge Base

Konvertiert die annotierte Wissensbasis (code-3.JSON) in produktionsreife
Golden Sets für NER und Classification Quality Assurance.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass
import logging

# Füge das src-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NEREntity:
    """Struktur für eine NER-Entität im Golden Set"""
    start: int
    end: int
    label: str
    text: str


@dataclass
class NERSample:
    """Ein vollständiges NER-Sample für das Golden Set"""
    text: str
    entities: List[NEREntity]
    source_document: str
    chunk_id: str


@dataclass
class ClassificationSample:
    """Ein Classification-Sample für das Golden Set"""
    text: str
    label: str
    source_document: str
    chunk_id: str


class GoldenSetGenerator:
    """
    Generiert Golden Sets aus der strukturierten Wissensbasis.
    """
    
    def __init__(self, knowledge_base_path: Path):
        self.knowledge_base_path = knowledge_base_path
        self.valid_ner_labels = {
            'TECHNOLOGY', 'ORGANIZATION', 'STANDARD', 
            'CONTROL_ID', 'ROLE', 'PROCESS'
        }
        self.valid_classification_labels = {
            'BSI_GRUNDSCHUTZ', 'BSI_STANDARD', 'BSI_C5', 
            'ISO_27001', 'NIST_CSF', 'TECHNICAL_DOC', 
            'WHITEPAPER', 'FAQ', 'UNKNOWN'
        }
        
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Lädt die Wissensbasis-JSON-Datei"""
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(f"Wissensbasis nicht gefunden: {self.knowledge_base_path}")
        
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Wissensbasis erfolgreich geladen: {self.knowledge_base_path}")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültiges JSON in Wissensbasis: {e}")
    
    def validate_ner_entity(self, entity: Dict[str, Any], text: str) -> bool:
        """Validiert eine NER-Entität"""
        required_fields = ['start', 'end', 'label']
        
        # Prüfe Pflichtfelder
        if not all(field in entity for field in required_fields):
            logger.warning(f"NER-Entität fehlen Pflichtfelder: {entity}")
            return False
        
        # Prüfe Label-Gültigkeit
        if entity['label'] not in self.valid_ner_labels:
            logger.warning(f"Ungültiges NER-Label: {entity['label']}")
            return False
        
        # Prüfe Position-Konsistenz
        start, end = entity['start'], entity['end']
        if start < 0 or end > len(text) or start >= end:
            logger.warning(f"Ungültige Positionen: start={start}, end={end}, text_len={len(text)}")
            return False
        
        return True
    
    def extract_ner_samples(self, knowledge_base: Dict[str, Any]) -> List[NERSample]:
        """Extrahiert NER-Samples aus der Wissensbasis"""
        samples = []
        documents = knowledge_base.get("knowledge_base_for_scripting", {}).get("documents", [])
        
        for doc in documents:
            doc_name = doc.get("document_name", "unknown")
            chunks = doc.get("representative_chunks", [])
            
            for i, chunk in enumerate(chunks):
                text = chunk.get("text")
                raw_entities = chunk.get("suggested_ner_entities", [])
                
                if not text or not raw_entities:
                    continue
                
                # Validiere und konvertiere Entitäten
                entities = []
                for entity_data in raw_entities:
                    if self.validate_ner_entity(entity_data, text):
                        start, end = entity_data['start'], entity_data['end']
                        entity_text = text[start:end]
                        
                        entities.append(NEREntity(
                            start=start,
                            end=end,
                            label=entity_data['label'],
                            text=entity_text
                        ))
                
                if entities:  # Nur Samples mit gültigen Entitäten
                    sample = NERSample(
                        text=text,
                        entities=entities,
                        source_document=doc_name,
                        chunk_id=f"{doc_name}_chunk_{i}"
                    )
                    samples.append(sample)
        
        logger.info(f"Extrahierte {len(samples)} NER-Samples")
        return samples
    
    def extract_classification_samples(self, knowledge_base: Dict[str, Any]) -> List[ClassificationSample]:
        """Extrahiert Classification-Samples aus der Wissensbasis"""
        samples = []
        documents = knowledge_base.get("knowledge_base_for_scripting", {}).get("documents", [])
        
        for doc in documents:
            doc_name = doc.get("document_name", "unknown")
            doc_type = doc.get("predicted_document_type")
            chunks = doc.get("representative_chunks", [])
            
            # Normalisiere Document Type auf gültige Labels
            normalized_label = self._normalize_classification_label(doc_type)
            if not normalized_label:
                logger.warning(f"Ungültiger Document Type: {doc_type}")
                continue
            
            for i, chunk in enumerate(chunks):
                text = chunk.get("text")
                if not text:
                    continue
                
                sample = ClassificationSample(
                    text=text,
                    label=normalized_label,
                    source_document=doc_name,
                    chunk_id=f"{doc_name}_chunk_{i}"
                )
                samples.append(sample)
        
        logger.info(f"Extrahierte {len(samples)} Classification-Samples")
        return samples
    
    def _normalize_classification_label(self, raw_label: str) -> str:
        """Normalisiert Classification-Labels"""
        if not raw_label:
            return "UNKNOWN"
        
        # Mapping von rohen Labels zu normalisierten Labels
        label_mapping = {
            "BSI_STANDARD": "BSI_STANDARD",
            "BSI_GRUNDSCHUTZ_BAUSTEIN": "BSI_GRUNDSCHUTZ",
            "ISO_STANDARD": "ISO_27001",
            "NIST_STANDARD": "NIST_CSF",
            "TECHNICAL_DOC": "TECHNICAL_DOC",
            "WHITEPAPER": "WHITEPAPER",
            "FAQ": "FAQ"
        }
        
        normalized = label_mapping.get(raw_label, "UNKNOWN")
        if normalized not in self.valid_classification_labels:
            return "UNKNOWN"
        
        return normalized
    
    def save_ner_golden_set(self, samples: List[NERSample], output_path: Path, version: str = "v1.0") -> None:
        """Speichert NER Golden Set als JSONL"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                # Konvertiere zu JSONL-Format
                jsonl_entry = {
                    "text": sample.text,
                    "entities": [
                        {
                            "start": entity.start,
                            "end": entity.end,
                            "label": entity.label,
                            "text": entity.text
                        }
                        for entity in sample.entities
                    ],
                    "metadata": {
                        "source_document": sample.source_document,
                        "chunk_id": sample.chunk_id,
                        "version": version
                    }
                }
                f.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"NER Golden Set gespeichert: {output_path} ({len(samples)} Samples)")
    
    def save_classification_golden_set(self, samples: List[ClassificationSample], output_path: Path, version: str = "v1.0") -> None:
        """Speichert Classification Golden Set als JSONL"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                jsonl_entry = {
                    "text": sample.text,
                    "label": sample.label,
                    "metadata": {
                        "source_document": sample.source_document,
                        "chunk_id": sample.chunk_id,
                        "version": version
                    }
                }
                f.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"Classification Golden Set gespeichert: {output_path} ({len(samples)} Samples)")
    
    def generate_statistics(self, ner_samples: List[NERSample], classification_samples: List[ClassificationSample]) -> Dict[str, Any]:
        """Generiert Statistiken über die Golden Sets"""
        
        # NER-Statistiken
        entity_label_counts = {}
        total_entities = 0
        
        for sample in ner_samples:
            for entity in sample.entities:
                entity_label_counts[entity.label] = entity_label_counts.get(entity.label, 0) + 1
                total_entities += 1
        
        # Classification-Statistiken
        classification_label_counts = {}
        for sample in classification_samples:
            classification_label_counts[sample.label] = classification_label_counts.get(sample.label, 0) + 1
        
        # Dokument-Statistiken
        ner_documents = set(sample.source_document for sample in ner_samples)
        classification_documents = set(sample.source_document for sample in classification_samples)
        
        return {
            "ner_statistics": {
                "total_samples": len(ner_samples),
                "total_entities": total_entities,
                "entity_label_distribution": entity_label_counts,
                "unique_documents": len(ner_documents),
                "avg_entities_per_sample": total_entities / len(ner_samples) if ner_samples else 0
            },
            "classification_statistics": {
                "total_samples": len(classification_samples),
                "label_distribution": classification_label_counts,
                "unique_documents": len(classification_documents)
            }
        }


def main():
    """Hauptfunktion zur Generierung der Golden Sets"""
    logger.info("🚀 Starte Golden Set Generierung aus code-3.JSON")
    
    # Pfade konfigurieren
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    knowledge_base_path = project_root / "code-3.JSON"
    output_dir = project_root / "quality_assurance" / "golden_sets"
    version = "v1.0"
    
    # Prüfe ob code-3.JSON existiert
    if not knowledge_base_path.exists():
        logger.error(f"❌ code-3.JSON nicht gefunden: {knowledge_base_path}")
        logger.info("   Bitte stellen Sie sicher, dass code-3.JSON im Projekt-Root liegt.")
        sys.exit(1)
    
    try:
        # Golden Set Generator initialisieren
        generator = GoldenSetGenerator(knowledge_base_path)
        
        # Wissensbasis laden
        knowledge_base = generator.load_knowledge_base()
        
        # Samples extrahieren
        ner_samples = generator.extract_ner_samples(knowledge_base)
        classification_samples = generator.extract_classification_samples(knowledge_base)
        
        if not ner_samples and not classification_samples:
            logger.error("❌ Keine gültigen Samples gefunden!")
            sys.exit(1)
        
        # Golden Sets speichern
        if ner_samples:
            ner_output_path = output_dir / f"golden_set_ner_{version}.jsonl"
            generator.save_ner_golden_set(ner_samples, ner_output_path, version)
        
        if classification_samples:
            classification_output_path = output_dir / f"golden_set_classification_{version}.jsonl"
            generator.save_classification_golden_set(classification_samples, classification_output_path, version)
        
        # Statistiken generieren und anzeigen
        stats = generator.generate_statistics(ner_samples, classification_samples)
        
        logger.info("\n" + "="*60)
        logger.info("📊 GOLDEN SET STATISTIKEN")
        logger.info("="*60)
        
        if ner_samples:
            ner_stats = stats["ner_statistics"]
            logger.info(f"NER Golden Set:")
            logger.info(f"  - Samples: {ner_stats['total_samples']}")
            logger.info(f"  - Entitäten: {ner_stats['total_entities']}")
            logger.info(f"  - Ø Entitäten/Sample: {ner_stats['avg_entities_per_sample']:.1f}")
            logger.info(f"  - Dokumente: {ner_stats['unique_documents']}")
            logger.info("  - Label-Verteilung:")
            for label, count in sorted(ner_stats['entity_label_distribution'].items()):
                logger.info(f"    • {label}: {count}")
        
        if classification_samples:
            cls_stats = stats["classification_statistics"]
            logger.info(f"\nClassification Golden Set:")
            logger.info(f"  - Samples: {cls_stats['total_samples']}")
            logger.info(f"  - Dokumente: {cls_stats['unique_documents']}")
            logger.info("  - Label-Verteilung:")
            for label, count in sorted(cls_stats['label_distribution'].items()):
                logger.info(f"    • {label}: {count}")
        
        logger.info("="*60)
        logger.info("✅ Golden Set Generierung erfolgreich abgeschlossen!")
        logger.info(f"📁 Output-Verzeichnis: {output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Golden Set Generierung: {e}")
        raise


if __name__ == "__main__":
    main() 