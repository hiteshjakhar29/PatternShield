"""
PatternShield API Server
Flask API with multiple detection models.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Import detectors
from ml_detector import DarkPatternDetector
from transformer_detector import TransformerDetector, EnsembleDetector

app = Flask(__name__)
CORS(app)

# Initialize detectors
rule_detector = DarkPatternDetector()

# Transformer detector (load only if model exists)
transformer_available = os.path.exists('models/distilbert_darkpattern/best_model')
if transformer_available:
    print("Loading transformer model...")
    transformer_detector = TransformerDetector()
    ensemble_detector = EnsembleDetector()
    print("Transformer model loaded successfully")
else:
    print("Transformer model not found. Only rule-based detection available.")
    print("Train the model first: bash scripts/train.sh")
    transformer_detector = None
    ensemble_detector = None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'models': {
            'rule_based': True,
            'transformer': transformer_available,
            'ensemble': transformer_available
        }
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze text using rule-based detector."""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    element_type = data.get('element_type', 'div')
    color = data.get('color', '#000000')
    
    result = rule_detector.analyze_element(text, element_type, color)
    
    return jsonify({
        'text': text,
        'primary_pattern': result['primary_pattern'],
        'detected_patterns': result['detected_patterns'],
        'confidence_scores': result['confidence_scores'],
        'sentiment': result['sentiment'],
        'method': 'rule_based'
    })


@app.route('/analyze/transformer', methods=['POST'])
def analyze_transformer():
    """Analyze text using transformer model."""
    if not transformer_available:
        return jsonify({
            'error': 'Transformer model not available',
            'message': 'Train the model first using: bash scripts/train.sh'
        }), 503
    
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    
    result = transformer_detector.predict(text, return_probabilities=True)
    
    return jsonify({
        'text': result['text'],
        'label': result['label'],
        'confidence': result['confidence'],
        'probabilities': result['probabilities'],
        'method': 'transformer'
    })


@app.route('/analyze/ensemble', methods=['POST'])
def analyze_ensemble():
    """Analyze text using ensemble of transformer and rule-based."""
    if not transformer_available:
        return jsonify({
            'error': 'Ensemble not available (transformer model missing)',
            'message': 'Train the model first using: bash scripts/train.sh'
        }), 503
    
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    element_type = data.get('element_type', 'div')
    color = data.get('color', '#000000')
    
    result = ensemble_detector.predict(text, element_type, color)
    
    return jsonify({
        'text': result['text'],
        'label': result['label'],
        'confidence': result['confidence'],
        'probabilities': result['probabilities'],
        'transformer_prediction': result['transformer_prediction'],
        'rule_based_prediction': result['rule_based_prediction'],
        'method': 'ensemble'
    })


@app.route('/analyze/compare', methods=['POST'])
def analyze_compare():
    """Compare predictions from all available models."""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    element_type = data.get('element_type', 'div')
    color = data.get('color', '#000000')
    
    # Rule-based
    rule_result = rule_detector.analyze_element(text, element_type, color)
    
    response = {
        'text': text,
        'rule_based': {
            'label': rule_result['primary_pattern'] if rule_result['primary_pattern'] else 'No Pattern',
            'confidence': max(rule_result['confidence_scores'].values()) if rule_result['confidence_scores'] else 0.0,
            'all_patterns': rule_result['detected_patterns']
        }
    }
    
    # Transformer (if available)
    if transformer_available:
        trans_result = transformer_detector.predict(text)
        response['transformer'] = {
            'label': trans_result['label'],
            'confidence': trans_result['confidence']
        }
        
        # Ensemble
        ensemble_result = ensemble_detector.predict(text, element_type, color)
        response['ensemble'] = {
            'label': ensemble_result['label'],
            'confidence': ensemble_result['confidence']
        }
    
    return jsonify(response)


@app.route('/batch/analyze', methods=['POST'])
def batch_analyze():
    """Batch analysis endpoint."""
    data = request.get_json()
    
    if not data or 'texts' not in data:
        return jsonify({'error': 'No texts provided'}), 400
    
    texts = data['texts']
    model_type = data.get('model', 'rule_based')
    
    results = []
    
    for text in texts:
        if model_type == 'transformer' and transformer_available:
            result = transformer_detector.predict(text)
        elif model_type == 'ensemble' and transformer_available:
            result = ensemble_detector.predict(text)
        else:
            # Default to rule-based
            result = rule_detector.analyze_element(text)
            result = {
                'text': text,
                'label': result['primary_pattern'] if result['primary_pattern'] else 'No Pattern',
                'confidence': max(result['confidence_scores'].values()) if result['confidence_scores'] else 0.0
            }
        
        results.append(result)
    
    return jsonify({
        'results': results,
        'model': model_type,
        'count': len(results)
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("PatternShield API Server")
    print("="*60)
    print(f"Rule-based model: ✓")
    print(f"Transformer model: {'✓' if transformer_available else '✗ (not trained)'}")
    print(f"Ensemble model: {'✓' if transformer_available else '✗ (not trained)'}")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET  /health")
    print("  POST /analyze")
    print("  POST /analyze/transformer")
    print("  POST /analyze/ensemble")
    print("  POST /analyze/compare")
    print("  POST /batch/analyze")
    print("\nStarting server...")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
