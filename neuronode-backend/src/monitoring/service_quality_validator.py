"""
Service Quality Validator

Produktionsreifer Quality Assurance Service für NER und Classification Services.
Validiert Services gegen Golden Sets und berechnet echte Metriken.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter
import asyncio
import time

# Lokale Imports
from ..processing.gemini_entity_extractor import GeminiEntityExtractor
from ..document_processing.document_processor import DocumentProcessor
from ..config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class EntityPrediction:
    """Predicted NER Entity"""
    start: int
    end: int
    label: str
    text: str
    confidence: float = 1.0


@dataclass
class ClassificationPrediction:
    """Predicted Classification"""
    label: str
    confidence: float = 1.0


@dataclass
class NERMetrics:
    """NER Evaluation Metrics"""
    precision: float
    recall: float
    f1_score: float
    support: int
    label_metrics: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClassificationMetrics:
    """Classification Evaluation Metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    support: int
    confusion_matrix: Dict[str, Dict[str, int]]
    label_metrics: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityReport:
    """Complete Quality Assessment Report"""
    service_name: str
    evaluation_timestamp: str
    golden_set_version: str
    total_samples: int
    processing_time_ms: float
    error_rate: float
    ner_metrics: Optional[NERMetrics] = None
    classification_metrics: Optional[ClassificationMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GoldenSetLoader:
    """Loads and manages Golden Sets"""
    
    def __init__(self, golden_sets_dir: Path):
        self.golden_sets_dir = golden_sets_dir
        
    def load_ner_golden_set(self, version: str = "v1.0") -> List[Dict[str, Any]]:
        """Load NER Golden Set"""
        golden_set_path = self.golden_sets_dir / f"golden_set_ner_{version}.jsonl"
        
        if not golden_set_path.exists():
            raise FileNotFoundError(f"NER Golden Set nicht gefunden: {golden_set_path}")
        
        samples = []
        with open(golden_set_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        
        logger.info(f"NER Golden Set geladen: {len(samples)} Samples")
        return samples
    
    def load_classification_golden_set(self, version: str = "v1.0") -> List[Dict[str, Any]]:
        """Load Classification Golden Set"""
        golden_set_path = self.golden_sets_dir / f"golden_set_classification_{version}.jsonl"
        
        if not golden_set_path.exists():
            raise FileNotFoundError(f"Classification Golden Set nicht gefunden: {golden_set_path}")
        
        samples = []
        with open(golden_set_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        
        logger.info(f"Classification Golden Set geladen: {len(samples)} Samples")
        return samples


class NEREvaluator:
    """Evaluates NER performance against Golden Set"""
    
    def __init__(self):
        self.valid_labels = {'TECHNOLOGY', 'ORGANIZATION', 'STANDARD', 'CONTROL_ID', 'ROLE', 'PROCESS'}
    
    def entities_overlap(self, pred_entity: EntityPrediction, true_entity: Dict[str, Any]) -> bool:
        """Check if predicted and true entities overlap"""
        pred_start, pred_end = pred_entity.start, pred_entity.end
        true_start, true_end = true_entity['start'], true_entity['end']
        
        # Overlap if intersection is non-empty
        return max(pred_start, true_start) < min(pred_end, true_end)
    
    def calculate_entity_metrics(self, predicted: List[EntityPrediction], 
                                true_entities: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """Calculate TP, FP, FN for entities"""
        true_positives = 0
        false_positives = 0
        
        # Convert to sets for easier matching
        matched_true = set()
        matched_pred = set()
        
        # Find matches (exact or overlapping)
        for i, pred in enumerate(predicted):
            for j, true_ent in enumerate(true_entities):
                if (j not in matched_true and 
                    pred.label == true_ent['label'] and
                    self.entities_overlap(pred, true_ent)):
                    true_positives += 1
                    matched_true.add(j)
                    matched_pred.add(i)
                    break
        
        # Count false positives (unmatched predictions)
        false_positives = len(predicted) - len(matched_pred)
        
        # Count false negatives (unmatched ground truth)
        false_negatives = len(true_entities) - len(matched_true)
        
        return true_positives, false_positives, false_negatives
    
    def calculate_metrics_per_label(self, predicted: List[EntityPrediction], 
                                   true_entities: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate precision, recall, F1 per label"""
        label_metrics = {}
        
        for label in self.valid_labels:
            # Filter by label
            pred_label = [p for p in predicted if p.label == label]
            true_label = [t for t in true_entities if t['label'] == label]
            
            if not pred_label and not true_label:
                continue
            
            tp, fp, fn = self.calculate_entity_metrics(pred_label, true_label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            label_metrics[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': len(true_label),
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn
            }
        
        return label_metrics
    
    def evaluate(self, predictions: List[List[EntityPrediction]], 
                golden_set: List[Dict[str, Any]]) -> NERMetrics:
        """Complete NER evaluation"""
        
        if len(predictions) != len(golden_set):
            raise ValueError(f"Predictions ({len(predictions)}) and Golden Set ({len(golden_set)}) size mismatch")
        
        # Aggregate metrics across all samples
        total_tp, total_fp, total_fn = 0, 0, 0
        all_label_metrics = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'support': 0})
        
        for pred_entities, sample in zip(predictions, golden_set):
            true_entities = sample['entities']
            
            # Sample-level metrics
            tp, fp, fn = self.calculate_entity_metrics(pred_entities, true_entities)
            total_tp += tp
            total_fp += fp
            total_fn += fn
            
            # Label-level metrics aggregation
            label_metrics = self.calculate_metrics_per_label(pred_entities, true_entities)
            for label, metrics in label_metrics.items():
                all_label_metrics[label]['tp'] += metrics['true_positives']
                all_label_metrics[label]['fp'] += metrics['false_positives']
                all_label_metrics[label]['fn'] += metrics['false_negatives']
                all_label_metrics[label]['support'] += metrics['support']
        
        # Calculate overall metrics
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
        
        # Calculate per-label metrics
        final_label_metrics = {}
        for label, counts in all_label_metrics.items():
            tp, fp, fn = counts['tp'], counts['fp'], counts['fn']
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            final_label_metrics[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': counts['support']
            }
        
        return NERMetrics(
            precision=overall_precision,
            recall=overall_recall,
            f1_score=overall_f1,
            support=total_tp + total_fn,
            label_metrics=final_label_metrics
        )


class ClassificationEvaluator:
    """Evaluates Classification performance against Golden Set"""
    
    def __init__(self):
        self.valid_labels = {
            'BSI_GRUNDSCHUTZ', 'BSI_STANDARD', 'BSI_C5', 
            'ISO_27001', 'NIST_CSF', 'TECHNICAL_DOC', 
            'WHITEPAPER', 'FAQ', 'UNKNOWN'
        }
    
    def evaluate(self, predictions: List[ClassificationPrediction], 
                golden_set: List[Dict[str, Any]]) -> ClassificationMetrics:
        """Complete Classification evaluation"""
        
        if len(predictions) != len(golden_set):
            raise ValueError(f"Predictions ({len(predictions)}) and Golden Set ({len(golden_set)}) size mismatch")
        
        # Extract true and predicted labels
        true_labels = [sample['label'] for sample in golden_set]
        pred_labels = [pred.label for pred in predictions]
        
        # Overall accuracy
        correct = sum(1 for true_label, pred_label in zip(true_labels, pred_labels) if true_label == pred_label)
        accuracy = correct / len(true_labels)
        
        # Confusion matrix
        confusion_matrix = defaultdict(lambda: defaultdict(int))
        for true_label, pred_label in zip(true_labels, pred_labels):
            confusion_matrix[true_label][pred_label] += 1
        
        # Per-label metrics
        label_metrics = {}
        all_labels = set(true_labels + pred_labels)
        
        macro_precision, macro_recall, macro_f1 = 0, 0, 0
        valid_labels_count = 0
        
        for label in all_labels:
            # True positives, false positives, false negatives
            tp = confusion_matrix[label][label]
            fp = sum(confusion_matrix[other_label][label] for other_label in all_labels if other_label != label)
            fn = sum(confusion_matrix[label][other_label] for other_label in all_labels if other_label != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            support = sum(1 for tl in true_labels if tl == label)
            
            label_metrics[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': support
            }
            
            if support > 0:  # Only count labels that exist in ground truth
                macro_precision += precision
                macro_recall += recall
                macro_f1 += f1
                valid_labels_count += 1
        
        # Macro averages
        macro_precision /= valid_labels_count if valid_labels_count > 0 else 1
        macro_recall /= valid_labels_count if valid_labels_count > 0 else 1
        macro_f1 /= valid_labels_count if valid_labels_count > 0 else 1
        
        # Convert confusion matrix to regular dict
        confusion_dict = {
            true_label: dict(pred_counts)
            for true_label, pred_counts in confusion_matrix.items()
        }
        
        return ClassificationMetrics(
            accuracy=accuracy,
            precision=macro_precision,
            recall=macro_recall,
            f1_score=macro_f1,
            support=len(true_labels),
            confusion_matrix=confusion_dict,
            label_metrics=label_metrics
        )


class ServiceQualityValidator:
    """
    Main Quality Validator for AI Services
    """
    
    def __init__(self, golden_sets_dir: Path, settings: Settings):
        self.golden_sets_dir = golden_sets_dir
        self.settings = settings
        self.golden_set_loader = GoldenSetLoader(golden_sets_dir)
        self.ner_evaluator = NEREvaluator()
        self.classification_evaluator = ClassificationEvaluator()
        
        # Initialize services
        self.gemini_extractor = GeminiEntityExtractor()
        self.document_processor = DocumentProcessor()
        
        logger.info(f"ServiceQualityValidator initialisiert mit Golden Sets: {golden_sets_dir}")
    
    def run_ner_predictions(self, texts: List[str]) -> List[List[EntityPrediction]]:
        """Run NER predictions on texts"""
        predictions = []
        
        for text in texts:
            try:
                # Use GeminiEntityExtractor (synchronous)
                extraction_result = self.gemini_extractor.extract_entities(text)
                
                # Convert to EntityPrediction objects
                entities = []
                for extracted_entity in extraction_result.entities:
                    entities.append(EntityPrediction(
                        start=extracted_entity.start_pos or 0,
                        end=extracted_entity.end_pos or len(extracted_entity.text),
                        label=extracted_entity.category,
                        text=extracted_entity.text,
                        confidence=extracted_entity.confidence
                    ))
                
                predictions.append(entities)
                
            except Exception as e:
                logger.error(f"NER Prediction Fehler: {e}")
                predictions.append([])  # Empty prediction on error
        
        return predictions
    
    def run_classification_predictions(self, texts: List[str]) -> List[ClassificationPrediction]:
        """Run Classification predictions on texts"""
        predictions = []
        
        for text in texts:
            try:
                # Use DocumentProcessor for classification
                result = self.document_processor.classify_document(text)
                
                predictions.append(ClassificationPrediction(
                    label=result.get('predicted_type', 'UNKNOWN'),
                    confidence=result.get('confidence', 1.0)
                ))
                
            except Exception as e:
                logger.error(f"Classification Prediction Fehler: {e}")
                predictions.append(ClassificationPrediction(label='UNKNOWN', confidence=0.0))
        
        return predictions
    
    def validate_ner_service(self, golden_set_version: str = "v1.0") -> QualityReport:
        """Validate NER Service against Golden Set"""
        logger.info(f"🔍 Starte NER Service Validation (Golden Set: {golden_set_version})")
        
        start_time = time.time()
        
        try:
            # Load Golden Set
            golden_set = self.golden_set_loader.load_ner_golden_set(golden_set_version)
            texts = [sample['text'] for sample in golden_set]
            
            # Run predictions
            predictions = self.run_ner_predictions(texts)
            
            # Count errors
            error_count = sum(1 for pred in predictions if not pred)
            error_rate = error_count / len(predictions)
            
            # Evaluate
            ner_metrics = self.ner_evaluator.evaluate(predictions, golden_set)
            
            processing_time = (time.time() - start_time) * 1000
            
            report = QualityReport(
                service_name="GeminiEntityExtractor",
                evaluation_timestamp=datetime.now().isoformat(),
                golden_set_version=golden_set_version,
                total_samples=len(golden_set),
                processing_time_ms=processing_time,
                error_rate=error_rate,
                ner_metrics=ner_metrics
            )
            
            logger.info(f"✅ NER Validation abgeschlossen - F1: {ner_metrics.f1_score:.3f}")
            return report
            
        except Exception as e:
            logger.error(f"❌ NER Validation fehlgeschlagen: {e}")
            raise
    
    def validate_classification_service(self, golden_set_version: str = "v1.0") -> QualityReport:
        """Validate Classification Service against Golden Set"""
        logger.info(f"🔍 Starte Classification Service Validation (Golden Set: {golden_set_version})")
        
        start_time = time.time()
        
        try:
            # Load Golden Set
            golden_set = self.golden_set_loader.load_classification_golden_set(golden_set_version)
            texts = [sample['text'] for sample in golden_set]
            
            # Run predictions
            predictions = self.run_classification_predictions(texts)
            
            # Count errors
            error_count = sum(1 for pred in predictions if pred.label == 'UNKNOWN' and pred.confidence == 0.0)
            error_rate = error_count / len(predictions)
            
            # Evaluate
            classification_metrics = self.classification_evaluator.evaluate(predictions, golden_set)
            
            processing_time = (time.time() - start_time) * 1000
            
            report = QualityReport(
                service_name="DocumentClassifier",
                evaluation_timestamp=datetime.now().isoformat(),
                golden_set_version=golden_set_version,
                total_samples=len(golden_set),
                processing_time_ms=processing_time,
                error_rate=error_rate,
                classification_metrics=classification_metrics
            )
            
            logger.info(f"✅ Classification Validation abgeschlossen - Accuracy: {classification_metrics.accuracy:.3f}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Classification Validation fehlgeschlagen: {e}")
            raise
    
    def save_quality_report(self, report: QualityReport, output_dir: Path) -> Path:
        """Save Quality Report to JSON file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_report_{report.service_name}_{timestamp}.json"
        report_path = output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Quality Report gespeichert: {report_path}")
        return report_path
    
    def run_full_validation(self, golden_set_version: str = "v1.0") -> Dict[str, QualityReport]:
        """Run complete validation of all services"""
        logger.info("🚀 Starte vollständige Service Validation")
        
        reports = {}
        
        try:
            # NER Validation
            ner_report = self.validate_ner_service(golden_set_version)
            reports['ner'] = ner_report
            
            # Classification Validation
            classification_report = self.validate_classification_service(golden_set_version)
            reports['classification'] = classification_report
            
            logger.info("✅ Vollständige Service Validation abgeschlossen")
            return reports
            
        except Exception as e:
            logger.error(f"❌ Vollständige Validation fehlgeschlagen: {e}")
            raise 