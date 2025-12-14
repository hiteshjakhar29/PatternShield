"""
Transformer-based Dark Pattern Detector
Inference wrapper for fine-tuned DistilBERT model with ensemble support.
"""

import importlib.util
import os
from typing import Dict, List, Tuple, Optional

TORCH_AVAILABLE = bool(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers"))

if TORCH_AVAILABLE:
    import torch  # type: ignore
    import numpy as np  # type: ignore
    from transformers import DistilBertTokenizer, DistilBertForSequenceClassification  # type: ignore

# Import rule-based detector
from backend.ml_detector import DarkPatternDetector


class TransformerDetector:
    """DistilBERT-based dark pattern detector."""

    @staticmethod
    def model_exists(model_path: str = 'models/distilbert_darkpattern/best_model') -> bool:
        return os.path.exists(model_path)
    
    def __init__(self, model_path='models/distilbert_darkpattern/best_model'):
        """Initialize transformer detector."""
        self.model_path = model_path
        if not TORCH_AVAILABLE:
            self.device = None
            self.model_available = False
            self.tokenizer = None
            self.model = None
            return
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Label mapping
        self.id2label = {
            0: 'Urgency/Scarcity',
            1: 'Confirmshaming',
            2: 'Obstruction',
            3: 'Visual Interference',
            4: 'Sneaking',
            5: 'No Pattern'
        }
        self.label2id = {v: k for k, v in self.id2label.items()}
        
        # Load model if available
        self.model_available = TORCH_AVAILABLE and os.path.exists(model_path)

        if self.model_available:
            print(f"Loading transformer model from {model_path}...")
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
            self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"Model loaded on {self.device}")
        else:
            print(f"Warning: Model not found at {model_path}")
            print("Run train_transformer.py first to train the model")
            self.tokenizer = None
            self.model = None
    
    def predict(self, text: str, return_probabilities: bool = False) -> Dict:
        """
        Predict dark pattern class for text.
        
        Args:
            text: Input text to analyze
            return_probabilities: Whether to return class probabilities
            
        Returns:
            Dictionary with prediction and confidence
        """
        if not self.model_available:
            return {
                'label': 'No Pattern',
                'confidence': 0.0,
                'error': 'Model not available'
            }
        
        # Tokenize
        inputs = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        # Move to device
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            # Get probabilities
            probs = torch.softmax(logits, dim=1)[0]
            confidence, predicted_class = torch.max(probs, dim=0)
            
            predicted_label = self.id2label[predicted_class.item()]
            confidence_score = confidence.item()
        
        result = {
            'label': predicted_label,
            'confidence': confidence_score,
            'text': text
        }
        
        if return_probabilities:
            result['probabilities'] = {
                self.id2label[i]: float(probs[i])
                for i in range(len(probs))
            }
        
        return result
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Predict for multiple texts."""
        return [self.predict(text) for text in texts]


class EnsembleDetector:
    """Ensemble of transformer and rule-based detectors."""
    
    def __init__(self, transformer_weight=0.6, rule_weight=0.4):
        """
        Initialize ensemble detector.
        
        Args:
            transformer_weight: Weight for transformer predictions
            rule_weight: Weight for rule-based predictions
        """
        self.transformer_weight = transformer_weight
        self.rule_weight = rule_weight
        
        # Initialize detectors
        self.transformer = TransformerDetector()
        self.rule_based = DarkPatternDetector()
        
        # Label mapping for consistency
        self.labels = [
            'Urgency/Scarcity',
            'Confirmshaming', 
            'Obstruction',
            'Visual Interference',
            'Sneaking',
            'No Pattern'
        ]
    
    def _normalize_rule_based_output(self, rule_result: Dict) -> Dict:
        """Convert rule-based output to match transformer format."""
        # Get primary pattern
        primary = rule_result.get('primary_pattern', 'No Pattern')
        
        if primary is None:
            primary = 'No Pattern'
        
        # Get confidence from rule-based scores
        confidence_scores = rule_result.get('confidence_scores', {})
        confidence = confidence_scores.get(primary, 0.5) if primary != 'No Pattern' else 0.3
        
        # Create probability distribution
        probabilities = {}
        for label in self.labels:
            if label == primary:
                probabilities[label] = confidence
            else:
                # Distribute remaining probability
                probabilities[label] = (1.0 - confidence) / (len(self.labels) - 1)
        
        return {
            'label': primary,
            'confidence': confidence,
            'probabilities': probabilities
        }
    
    def predict(self, text: str, element_type: str = 'div', 
                color: str = '#000000') -> Dict:
        """
        Ensemble prediction combining transformer and rule-based.
        
        Args:
            text: Input text
            element_type: HTML element type
            color: Element color
            
        Returns:
            Dictionary with ensemble prediction
        """
        # Get transformer prediction
        if self.transformer.model_available:
            transformer_result = self.transformer.predict(text, return_probabilities=True)
            transformer_probs = transformer_result['probabilities']
        else:
            # Fallback to uniform distribution
            transformer_probs = {label: 1.0/len(self.labels) for label in self.labels}
        
        # Get rule-based prediction
        rule_result = self.rule_based.analyze_element(text, element_type, color)
        rule_normalized = self._normalize_rule_based_output(rule_result)
        rule_probs = rule_normalized['probabilities']
        
        # Weighted ensemble
        ensemble_probs = {}
        for label in self.labels:
            trans_prob = transformer_probs.get(label, 0.0)
            rule_prob = rule_probs.get(label, 0.0)
            
            ensemble_probs[label] = (
                self.transformer_weight * trans_prob +
                self.rule_weight * rule_prob
            )
        
        # Get final prediction
        final_label = max(ensemble_probs.items(), key=lambda x: x[1])[0]
        final_confidence = ensemble_probs[final_label]
        
        return {
            'label': final_label,
            'confidence': final_confidence,
            'probabilities': ensemble_probs,
            'transformer_prediction': transformer_result.get('label', 'N/A') if self.transformer.model_available else 'N/A',
            'rule_based_prediction': rule_normalized['label'],
            'text': text,
            'method': 'ensemble'
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Batch prediction."""
        return [self.predict(text) for text in texts]


# Convenience functions
def predict_with_transformer(text: str) -> Tuple[str, float]:
    """
    Quick prediction using transformer only.
    
    Returns:
        (label, confidence)
    """
    detector = TransformerDetector()
    result = detector.predict(text)
    return result['label'], result['confidence']


def predict_with_ensemble(text: str, element_type: str = 'div',
                          color: str = '#000000') -> Tuple[str, float]:
    """
    Quick prediction using ensemble.
    
    Returns:
        (label, confidence)
    """
    detector = EnsembleDetector()
    result = detector.predict(text, element_type, color)
    return result['label'], result['confidence']


def compare_methods(text: str, element_type: str = 'div',
                   color: str = '#000000') -> Dict:
    """
    Compare all detection methods.
    
    Returns:
        Dictionary with predictions from all methods
    """
    # Rule-based
    rule_detector = DarkPatternDetector()
    rule_result = rule_detector.analyze_element(text, element_type, color)
    
    # Transformer
    trans_detector = TransformerDetector()
    trans_result = trans_detector.predict(text) if trans_detector.model_available else None
    
    # Ensemble
    ensemble_detector = EnsembleDetector()
    ensemble_result = ensemble_detector.predict(text, element_type, color)
    
    return {
        'text': text,
        'rule_based': {
            'label': rule_result.get('primary_pattern', 'No Pattern'),
            'confidence': max(rule_result.get('confidence_scores', {}).values()) if rule_result.get('confidence_scores') else 0.0
        },
        'transformer': {
            'label': trans_result['label'] if trans_result else 'N/A',
            'confidence': trans_result['confidence'] if trans_result else 0.0
        } if trans_result else None,
        'ensemble': {
            'label': ensemble_result['label'],
            'confidence': ensemble_result['confidence']
        }
    }


if __name__ == '__main__':
    # Test examples
    test_texts = [
        "Only 2 left in stock!",
        "No thanks, I don't want to save money",
        "To unsubscribe, mail a written request",
        "✓ Accept All ✗ Reject",
        "Add to cart"
    ]
    
    print("="*80)
    print("Testing Transformer Detector")
    print("="*80)
    
    detector = TransformerDetector()
    
    if detector.model_available:
        for text in test_texts:
            result = detector.predict(text)
            print(f"\nText: {text}")
            print(f"Prediction: {result['label']} (confidence: {result['confidence']:.3f})")
    else:
        print("\nModel not available. Train first using:")
        print("python train_transformer.py")
    
    print("\n" + "="*80)
    print("Testing Ensemble Detector")
    print("="*80)
    
    ensemble = EnsembleDetector()
    
    for text in test_texts:
        result = ensemble.predict(text)
        print(f"\nText: {text}")
        print(f"Ensemble: {result['label']} (conf: {result['confidence']:.3f})")
        print(f"Transformer: {result['transformer_prediction']}")
        print(f"Rule-based: {result['rule_based_prediction']}")
