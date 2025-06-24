from typing import List, Dict, Any, Tuple
from src.config.llm_config import llm_router, ModelPurpose
from src.models.document_types import ControlItem
from langchain.prompts import ChatPromptTemplate
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

logger = logging.getLogger(__name__)

class QualityValidator:
    """Cross-model validation for critical extractions"""
    
    def __init__(self):
        # Get two different models for validation
        self.validators = llm_router.get_model(ModelPurpose.VALIDATION)
        if not isinstance(self.validators, list) or len(self.validators) < 2:
            logger.warning("Less than 2 validators configured, using same model twice")
            primary = self.validators[0] if isinstance(self.validators, list) else self.validators
            self.validators = [primary, primary]
        
        self.validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Experte für die Validierung von extrahierten Compliance-Controls.
            
            Gegeben ist ein extrahiertes Control. Überprüfe:
            1. Ist die ID korrekt formatiert für den Standard {standard}?
            2. Ist der Titel sinnvoll und vollständig?
            3. Ist der Text vollständig erfasst (nicht abgeschnitten)?
            4. Stimmen Level und Domain (falls vorhanden)?
            
            Antworte im JSON-Format:
            {{
                "is_valid": true/false,
                "confidence": 0.0-1.0,
                "issues": ["Liste von Problemen"],
                "suggestions": {{"field": "suggested_value"}}
            }}"""),
            ("human", """Standard: {standard}
            
            Extrahiertes Control:
            ID: {control_id}
            Title: {title}
            Text: {text}
            Level: {level}
            Domain: {domain}""")
        ])
        
        self.comparison_prompt = ChatPromptTemplate.from_messages([
            ("system", """Vergleiche zwei Versionen eines extrahierten Controls.
            
            Bewerte:
            1. Stimmen die wichtigsten Felder (ID, Title) überein?
            2. Ist der Inhalt semantisch gleich?
            3. Welche Version ist vollständiger/besser?
            
            Antworte im JSON-Format:
            {{
                "match_score": 0.0-1.0,
                "matching_fields": ["id", "title", ...],
                "differences": ["field: difference description"],
                "preferred_version": 1 oder 2,
                "merge_suggestions": {{"field": "value"}}
            }}"""),
            ("human", """Version 1:
            {version1}
            
            Version 2:
            {version2}""")
        ])
    
    def validate_controls(
        self, 
        controls: List[ControlItem], 
        standard: str,
        confidence_threshold: float = 0.8
    ) -> Tuple[List[ControlItem], List[Dict[str, Any]]]:
        """Validate controls using multiple models"""
        
        validated_controls = []
        validation_reports = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit validation tasks
            future_to_control = {
                executor.submit(self._validate_single_control, control, standard): control
                for control in controls
            }
            
            for future in as_completed(future_to_control):
                control = future_to_control[future]
                try:
                    is_valid, report = future.result()
                    
                    if is_valid and report["confidence"] >= confidence_threshold:
                        validated_controls.append(control)
                    
                    validation_reports.append({
                        "control_id": control.id,
                        "valid": is_valid,
                        "report": report
                    })
                    
                except Exception as e:
                    logger.error(f"Error validating control {control.id}: {e}")
                    validation_reports.append({
                        "control_id": control.id,
                        "valid": False,
                        "error": str(e)
                    })
        
        logger.info(f"Validated {len(validated_controls)}/{len(controls)} controls")
        return validated_controls, validation_reports
    
    def _validate_single_control(self, control: ControlItem, standard: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate a single control"""
        
        # Get validation from first model
        validation1 = self._get_validation(control, standard, self.validators[0])
        
        # If high confidence, no need for second validation
        if validation1["is_valid"] and validation1["confidence"] > 0.95:
            return True, validation1
        
        # Get second opinion for uncertain cases
        validation2 = self._get_validation(control, standard, self.validators[1])
        
        # Combine validations
        combined = self._combine_validations(validation1, validation2)
        
        return combined["is_valid"], combined
    
    def _get_validation(self, control: ControlItem, standard: str, validator) -> Dict[str, Any]:
        """Get validation from a single model"""
        chain = self.validation_prompt | validator
        
        try:
            response = chain.invoke({
                "standard": standard,
                "control_id": control.id,
                "title": control.title,
                "text": control.text[:1000],  # Limit text length
                "level": control.level or "N/A",
                "domain": control.domain or "N/A"
            })
            
            # Parse JSON response
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "suggestions": {}
            }
    
    def _combine_validations(self, val1: Dict, val2: Dict) -> Dict[str, Any]:
        """Combine two validation results"""
        # Average confidence
        avg_confidence = (val1["confidence"] + val2["confidence"]) / 2
        
        # Combine issues
        all_issues = list(set(val1.get("issues", []) + val2.get("issues", [])))
        
        # Merge suggestions
        suggestions = {**val1.get("suggestions", {}), **val2.get("suggestions", {})}
        
        # Both must agree on validity
        is_valid = val1["is_valid"] and val2["is_valid"]
        
        return {
            "is_valid": is_valid,
            "confidence": avg_confidence,
            "issues": all_issues,
            "suggestions": suggestions,
            "validator_agreement": val1["is_valid"] == val2["is_valid"]
        }
    
    def cross_validate_extractions(
        self,
        extractions_model1: List[ControlItem],
        extractions_model2: List[ControlItem]
    ) -> Tuple[List[ControlItem], Dict[str, Any]]:
        """Cross-validate extractions from two different models"""
        
        # Create lookup dictionaries
        model1_dict = {c.id: c for c in extractions_model1}
        model2_dict = {c.id: c for c in extractions_model2}
        
        validated_controls = []
        comparison_report = {
            "total_model1": len(extractions_model1),
            "total_model2": len(extractions_model2),
            "matched": 0,
            "conflicts": [],
            "model1_only": [],
            "model2_only": []
        }
        
        # Process controls that exist in both
        common_ids = set(model1_dict.keys()) & set(model2_dict.keys())
        for control_id in common_ids:
            control1 = model1_dict[control_id]
            control2 = model2_dict[control_id]
            
            comparison = self._compare_controls(control1, control2)
            
            if comparison["match_score"] > 0.9:
                # High agreement - use the preferred version
                if comparison["preferred_version"] == 1:
                    validated_controls.append(control1)
                else:
                    validated_controls.append(control2)
                comparison_report["matched"] += 1
            else:
                # Conflict - needs manual review or merging
                comparison_report["conflicts"].append({
                    "control_id": control_id,
                    "comparison": comparison
                })
        
        # Track controls only in one model
        comparison_report["model1_only"] = list(set(model1_dict.keys()) - set(model2_dict.keys()))
        comparison_report["model2_only"] = list(set(model2_dict.keys()) - set(model1_dict.keys()))
        
        return validated_controls, comparison_report
    
    def _compare_controls(self, control1: ControlItem, control2: ControlItem) -> Dict[str, Any]:
        """Compare two versions of the same control"""
        chain = self.comparison_prompt | self.validators[0]
        
        try:
            response = chain.invoke({
                "version1": json.dumps(control1.dict(), indent=2),
                "version2": json.dumps(control2.dict(), indent=2)
            })
            
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"Comparison error: {e}")
            # Fallback to simple comparison
            return {
                "match_score": 0.8 if control1.title == control2.title else 0.5,
                "matching_fields": ["id"],
                "differences": ["Automated comparison failed"],
                "preferred_version": 1,
                "merge_suggestions": {}
            }