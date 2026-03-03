"""
Feature Extraction for Dark Pattern Detection
Comprehensive feature engineering pipeline.
"""

import re
import json
import numpy as np
from typing import Dict, List, Tuple
from textblob import TextBlob
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer


class FeatureExtractor:
    """Extract comprehensive features from UI elements."""
    
    def __init__(self, max_tfidf_features=100):
        """Initialize feature extractor."""
        self.max_tfidf_features = max_tfidf_features
        self.tfidf_vectorizer = None
        self.feature_names = []
        
        # Urgency keywords
        self.urgency_keywords = {
            'only', 'left', 'last', 'hurry', 'limited', 'now', 'soon', 
            'expires', 'ends', 'quick', 'fast', 'today', 'urgent'
        }
        
        # Negative words
        self.negative_words = {
            "don't", 'no', 'not', 'never', 'without', 'inferior', 
            'worse', 'poor', 'bad', 'waste'
        }
        
        # Element type encoding
        self.element_types = [
            'div', 'span', 'button', 'a', 'p', 'h1', 'h2', 'h3',
            'input', 'label', 'form', 'section'
        ]
        
    def fit_tfidf(self, texts: List[str]):
        """Fit TF-IDF vectorizer on corpus."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_tfidf_features,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_vectorizer.fit(texts)
        
    def extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract text-based features."""
        features = {}
        text_lower = text.lower()
        
        # Basic text statistics
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['avg_word_length'] = np.mean([len(w) for w in text.split()]) if text.split() else 0
        features['char_count'] = len(text)
        
        # Capitalization
        features['capital_ratio'] = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
        features['all_caps_words'] = sum(1 for w in text.split() if w.isupper())
        
        # Punctuation
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['emoji_count'] = len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]|[\u2600-\u27BF]', text))
        features['special_char_ratio'] = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text) if len(text) > 0 else 0
        
        # Keyword density
        words = text_lower.split()
        features['urgency_keyword_count'] = sum(1 for w in words if w in self.urgency_keywords)
        features['urgency_keyword_density'] = features['urgency_keyword_count'] / len(words) if words else 0
        features['negative_word_count'] = sum(1 for w in words if w in self.negative_words)
        features['negative_word_density'] = features['negative_word_count'] / len(words) if words else 0
        
        # Numeric mentions
        features['numeric_count'] = len(re.findall(r'\d+', text))
        features['has_currency'] = 1 if re.search(r'[\$£€¥]', text) else 0
        features['has_percentage'] = 1 if '%' in text else 0
        
        # Sentiment analysis
        try:
            blob = TextBlob(text)
            features['sentiment_polarity'] = blob.sentiment.polarity
            features['sentiment_subjectivity'] = blob.sentiment.subjectivity
        except:
            features['sentiment_polarity'] = 0.0
            features['sentiment_subjectivity'] = 0.0
        
        # Readability
        try:
            features['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
            features['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
        except:
            features['flesch_reading_ease'] = 0.0
            features['flesch_kincaid_grade'] = 0.0
        
        return features
    
    def extract_visual_features(self, color: str) -> Dict[str, float]:
        """Extract visual/color features."""
        features = {}
        
        # Parse hex color
        try:
            if color.startswith('#'):
                color = color[1:]
            r = int(color[0:2], 16) / 255.0
            g = int(color[2:4], 16) / 255.0
            b = int(color[4:6], 16) / 255.0
        except:
            r, g, b = 0.0, 0.0, 0.0
        
        # RGB values
        features['color_r'] = r
        features['color_g'] = g
        features['color_b'] = b
        
        # HSL conversion
        max_rgb = max(r, g, b)
        min_rgb = min(r, g, b)
        l = (max_rgb + min_rgb) / 2.0
        
        if max_rgb == min_rgb:
            h = s = 0.0
        else:
            d = max_rgb - min_rgb
            s = d / (2.0 - max_rgb - min_rgb) if l > 0.5 else d / (max_rgb + min_rgb)
            
            if max_rgb == r:
                h = ((g - b) / d + (6 if g < b else 0)) / 6.0
            elif max_rgb == g:
                h = ((b - r) / d + 2) / 6.0
            else:
                h = ((r - g) / d + 4) / 6.0
        
        features['color_hue'] = h
        features['color_saturation'] = s
        features['color_lightness'] = l
        
        # Luminance (perceived brightness)
        features['color_luminance'] = 0.299 * r + 0.587 * g + 0.114 * b
        
        # Grayscale check
        features['is_grayscale'] = 1.0 if abs(r - g) < 0.1 and abs(g - b) < 0.1 else 0.0
        
        # Color dominance
        features['red_dominant'] = 1.0 if r > g and r > b else 0.0
        features['green_dominant'] = 1.0 if g > r and g > b else 0.0
        features['blue_dominant'] = 1.0 if b > r and b > g else 0.0
        
        # Brightness category
        features['is_bright'] = 1.0 if l > 0.7 else 0.0
        features['is_dark'] = 1.0 if l < 0.3 else 0.0
        
        # Saturation category
        features['is_saturated'] = 1.0 if s > 0.5 else 0.0
        features['is_desaturated'] = 1.0 if s < 0.3 else 0.0
        
        return features
    
    def extract_structural_features(self, element_type: str) -> Dict[str, float]:
        """Extract structural/element features."""
        features = {}
        
        # One-hot encoding for element type
        for et in self.element_types:
            features[f'element_type_{et}'] = 1.0 if element_type == et else 0.0
        
        # Element is unknown
        features['element_type_unknown'] = 1.0 if element_type not in self.element_types else 0.0
        
        # Interactive elements
        interactive = {'button', 'a', 'input', 'select', 'textarea'}
        features['is_interactive'] = 1.0 if element_type in interactive else 0.0
        
        # Text containers
        text_containers = {'p', 'span', 'div', 'h1', 'h2', 'h3', 'label'}
        features['is_text_container'] = 1.0 if element_type in text_containers else 0.0
        
        # Implied prominence (buttons and links are prominent)
        prominent = {'button', 'a', 'h1', 'h2'}
        features['is_prominent'] = 1.0 if element_type in prominent else 0.0
        
        # Size estimation (rough heuristic)
        large_elements = {'div', 'section', 'form'}
        small_elements = {'span', 'a', 'label'}
        features['implied_size_large'] = 1.0 if element_type in large_elements else 0.0
        features['implied_size_small'] = 1.0 if element_type in small_elements else 0.0
        features['implied_size_medium'] = 1.0 if element_type not in large_elements and element_type not in small_elements else 0.0
        
        return features
    
    def extract_tfidf_features(self, text: str) -> Dict[str, float]:
        """Extract TF-IDF features."""
        if self.tfidf_vectorizer is None:
            return {}
        
        try:
            tfidf_vector = self.tfidf_vectorizer.transform([text]).toarray()[0]
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            return {
                f'tfidf_{name}': float(value)
                for name, value in zip(feature_names, tfidf_vector)
            }
        except:
            return {f'tfidf_{name}': 0.0 for name in self.tfidf_vectorizer.get_feature_names_out()}
    
    def extract_features(self, text: str, element_type: str = 'div', 
                        color: str = '#000000', include_tfidf: bool = False) -> Dict[str, float]:
        """
        Extract all features from element.
        
        Args:
            text: Element text content
            element_type: HTML element type
            color: Hex color code
            include_tfidf: Whether to include TF-IDF features
            
        Returns:
            Dictionary of feature_name: value
        """
        features = {}
        
        # Extract feature groups
        features.update(self.extract_text_features(text))
        features.update(self.extract_visual_features(color))
        features.update(self.extract_structural_features(element_type))
        
        if include_tfidf:
            features.update(self.extract_tfidf_features(text))
        
        return features
    
    def get_feature_names(self, include_tfidf: bool = False) -> List[str]:
        """Get ordered list of feature names."""
        # Extract from dummy element to get feature names
        dummy_features = self.extract_features("test", "div", "#000000", include_tfidf=include_tfidf)
        return sorted(dummy_features.keys())
    
    def features_to_vector(self, features: Dict[str, float], 
                          feature_names: List[str] = None) -> np.ndarray:
        """Convert feature dict to numpy array."""
        if feature_names is None:
            feature_names = sorted(features.keys())
        
        return np.array([features.get(name, 0.0) for name in feature_names])
    
    def save_feature_definitions(self, output_path: str):
        """Save feature definitions to JSON."""
        definitions = {
            'text_features': {
                'text_length': 'Total character count',
                'word_count': 'Number of words',
                'avg_word_length': 'Average word length',
                'capital_ratio': 'Ratio of capital letters to total',
                'all_caps_words': 'Count of fully capitalized words',
                'exclamation_count': 'Number of exclamation marks',
                'question_count': 'Number of question marks',
                'emoji_count': 'Number of emojis/special unicode',
                'special_char_ratio': 'Ratio of special characters',
                'urgency_keyword_count': 'Count of urgency keywords',
                'urgency_keyword_density': 'Urgency keywords per word',
                'negative_word_count': 'Count of negative words',
                'negative_word_density': 'Negative words per word',
                'numeric_count': 'Count of numeric mentions',
                'has_currency': 'Binary: contains currency symbol',
                'has_percentage': 'Binary: contains percentage',
                'sentiment_polarity': 'Sentiment polarity (-1 to 1)',
                'sentiment_subjectivity': 'Sentiment subjectivity (0 to 1)',
                'flesch_reading_ease': 'Flesch reading ease score',
                'flesch_kincaid_grade': 'Flesch-Kincaid grade level'
            },
            'visual_features': {
                'color_r': 'Red channel (0-1)',
                'color_g': 'Green channel (0-1)',
                'color_b': 'Blue channel (0-1)',
                'color_hue': 'HSL hue (0-1)',
                'color_saturation': 'HSL saturation (0-1)',
                'color_lightness': 'HSL lightness (0-1)',
                'color_luminance': 'Perceived brightness',
                'is_grayscale': 'Binary: grayscale color',
                'red_dominant': 'Binary: red is dominant',
                'green_dominant': 'Binary: green is dominant',
                'blue_dominant': 'Binary: blue is dominant',
                'is_bright': 'Binary: bright color',
                'is_dark': 'Binary: dark color',
                'is_saturated': 'Binary: saturated color',
                'is_desaturated': 'Binary: desaturated color'
            },
            'structural_features': {
                'element_type_*': 'One-hot: element type',
                'is_interactive': 'Binary: interactive element',
                'is_text_container': 'Binary: text container',
                'is_prominent': 'Binary: visually prominent',
                'implied_size_large': 'Binary: large element',
                'implied_size_small': 'Binary: small element',
                'implied_size_medium': 'Binary: medium element'
            },
            'feature_counts': {
                'text_features': 21,
                'visual_features': 15,
                'structural_features': len(self.element_types) + 7,
                'total_base': 21 + 15 + len(self.element_types) + 7,
                'tfidf_features': self.max_tfidf_features
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(definitions, f, indent=2)
        
        print(f"Feature definitions saved to {output_path}")


if __name__ == '__main__':
    # Test feature extraction
    extractor = FeatureExtractor()
    
    # Test examples
    examples = [
        ("Only 2 left in stock!", "span", "#ef4444"),
        ("No thanks, I don't want to save money", "button", "#6b7280"),
        ("Add to cart", "button", "#3b82f6")
    ]
    
    print("="*80)
    print("Feature Extraction Test")
    print("="*80)
    
    for text, elem_type, color in examples:
        print(f"\nText: {text}")
        print(f"Element: {elem_type}, Color: {color}")
        
        features = extractor.extract_features(text, elem_type, color)
        print(f"Extracted {len(features)} features")
        
        # Show sample features
        sample_keys = list(features.keys())[:5]
        for key in sample_keys:
            print(f"  {key}: {features[key]:.4f}")
    
    # Save feature definitions
    extractor.save_feature_definitions('features_definition.json')
    
    print(f"\n✓ Feature extraction complete")
    print(f"Total features: {len(extractor.get_feature_names())}")
