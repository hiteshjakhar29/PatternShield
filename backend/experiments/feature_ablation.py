"""
Feature Ablation Study
Systematic removal of feature groups to measure impact.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from scipy.stats import chi2_contingency
from typing import Dict, List
import os

from feature_extraction import FeatureExtractor

np.random.seed(42)


class FeatureAblation:
    """Systematic feature ablation study."""
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.feature_names = []
        self.X = None
        self.y = None
        self.results = {}
        
        # Define feature groups
        self.feature_groups = {
            'text': [
                'text_length', 'word_count', 'avg_word_length', 'char_count',
                'capital_ratio', 'all_caps_words', 'exclamation_count',
                'question_count', 'emoji_count', 'special_char_ratio',
                'urgency_keyword_count', 'urgency_keyword_density',
                'negative_word_count', 'negative_word_density',
                'numeric_count', 'has_currency', 'has_percentage',
                'sentiment_polarity', 'sentiment_subjectivity',
                'flesch_reading_ease', 'flesch_kincaid_grade'
            ],
            'visual': [
                'color_r', 'color_g', 'color_b', 'color_hue',
                'color_saturation', 'color_lightness', 'color_luminance',
                'is_grayscale', 'red_dominant', 'green_dominant',
                'blue_dominant', 'is_bright', 'is_dark',
                'is_saturated', 'is_desaturated'
            ],
            'structural': [
                'element_type_', 'is_interactive', 'is_text_container',
                'is_prominent', 'implied_size_'
            ]
        }
    
    def load_data(self, data_path='data/training_dataset.json'):
        """Load and prepare data."""
        print(f"Loading data from {data_path}...")
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        all_examples = data['train'] + data['validation']
        texts = [ex['text'] for ex in all_examples]
        
        self.extractor.fit_tfidf(texts)
        
        feature_dicts = []
        labels = []
        
        label_map = {
            'Urgency/Scarcity': 0,
            'Confirmshaming': 1,
            'Obstruction': 2,
            'Visual Interference': 3,
            'Sneaking': 4,
            'No Pattern': 5
        }
        
        for ex in all_examples:
            features = self.extractor.extract_features(
                ex['text'],
                ex.get('element_type', 'div'),
                ex.get('color', '#000000'),
                include_tfidf=False
            )
            feature_dicts.append(features)
            labels.append(label_map[ex['label']])
        
        self.feature_names = sorted(feature_dicts[0].keys())
        self.X = np.array([[fd[name] for name in self.feature_names] 
                          for fd in feature_dicts])
        self.y = np.array(labels)
        
        print(f"Data shape: {self.X.shape}")
        return self.X, self.y
    
    def get_feature_indices(self, group_name: str) -> List[int]:
        """Get indices of features in a group."""
        group_keywords = self.feature_groups[group_name]
        indices = []
        
        for i, name in enumerate(self.feature_names):
            if any(keyword in name for keyword in group_keywords):
                indices.append(i)
        
        return indices
    
    def evaluate_feature_set(self, feature_indices: List[int], 
                            description: str) -> Dict:
        """Evaluate model with specific features."""
        if len(feature_indices) == 0:
            return {
                'f1_mean': 0.0,
                'f1_std': 0.0,
                'num_features': 0,
                'description': description
            }
        
        X_subset = self.X[:, feature_indices]
        
        rf = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        
        scores = cross_val_score(
            rf, X_subset, self.y,
            cv=5,
            scoring='f1_macro'
        )
        
        return {
            'f1_mean': float(scores.mean()),
            'f1_std': float(scores.std()),
            'num_features': len(feature_indices),
            'description': description
        }
    
    def ablation_study(self):
        """Run systematic ablation study."""
        print("\n" + "="*80)
        print("FEATURE ABLATION STUDY")
        print("="*80)
        
        # Baseline: All features
        print("\n1. Baseline (All Features)")
        all_indices = list(range(len(self.feature_names)))
        self.results['all'] = self.evaluate_feature_set(
            all_indices,
            "All features"
        )
        print(f"   F1: {self.results['all']['f1_mean']:.4f} ± "
              f"{self.results['all']['f1_std']:.4f}")
        
        baseline_f1 = self.results['all']['f1_mean']
        
        # Remove each group
        for group_name in ['text', 'visual', 'structural']:
            print(f"\n2. Without {group_name.capitalize()} Features")
            
            remove_indices = set(self.get_feature_indices(group_name))
            keep_indices = [i for i in all_indices if i not in remove_indices]
            
            key = f'without_{group_name}'
            self.results[key] = self.evaluate_feature_set(
                keep_indices,
                f"All except {group_name}"
            )
            
            f1 = self.results[key]['f1_mean']
            drop = baseline_f1 - f1
            print(f"   F1: {f1:.4f} ± {self.results[key]['f1_std']:.4f}")
            print(f"   Drop: {drop:.4f} ({drop/baseline_f1*100:.2f}%)")
            self.results[key]['f1_drop'] = float(drop)
            self.results[key]['f1_drop_pct'] = float(drop/baseline_f1*100)
        
        # Only each group
        for group_name in ['text', 'visual', 'structural']:
            print(f"\n3. Only {group_name.capitalize()} Features")
            
            indices = self.get_feature_indices(group_name)
            key = f'only_{group_name}'
            self.results[key] = self.evaluate_feature_set(
                indices,
                f"Only {group_name}"
            )
            
            f1 = self.results[key]['f1_mean']
            print(f"   F1: {f1:.4f} ± {self.results[key]['f1_std']:.4f}")
            print(f"   vs Baseline: {f1 - baseline_f1:.4f}")
        
        # Top features
        print("\n4. Top K Features (by importance)")
        
        # Train RF to get importances
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(self.X, self.y)
        importances = rf.feature_importances_
        
        for k in [10, 20, 30]:
            top_indices = np.argsort(importances)[::-1][:k]
            key = f'top_{k}'
            self.results[key] = self.evaluate_feature_set(
                top_indices.tolist(),
                f"Top {k} features"
            )
            
            f1 = self.results[key]['f1_mean']
            drop = baseline_f1 - f1
            print(f"\n   Top {k}: F1 = {f1:.4f} ± {self.results[key]['f1_std']:.4f}")
            print(f"   Drop: {drop:.4f} ({drop/baseline_f1*100:.2f}%)")
            self.results[key]['f1_drop'] = float(drop)
            self.results[key]['f1_drop_pct'] = float(drop/baseline_f1*100)
    
    def plot_ablation_results(self):
        """Visualize ablation results."""
        # Prepare data
        experiments = [
            'all',
            'without_text', 'without_visual', 'without_structural',
            'only_text', 'only_visual', 'only_structural',
            'top_10', 'top_20', 'top_30'
        ]
        
        labels = [
            'All Features',
            'No Text', 'No Visual', 'No Structural',
            'Only Text', 'Only Visual', 'Only Structural',
            'Top 10', 'Top 20', 'Top 30'
        ]
        
        f1_scores = [self.results[exp]['f1_mean'] for exp in experiments]
        f1_stds = [self.results[exp]['f1_std'] for exp in experiments]
        num_features = [self.results[exp]['num_features'] for exp in experiments]
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # F1 scores
        colors = ['green'] + ['red']*3 + ['blue']*3 + ['purple']*3
        bars = ax1.barh(range(len(experiments)), f1_scores, xerr=f1_stds, 
                       color=colors, alpha=0.7, capsize=5)
        ax1.set_yticks(range(len(experiments)))
        ax1.set_yticklabels(labels)
        ax1.set_xlabel('F1 Score (5-Fold CV)', fontsize=12, fontweight='bold')
        ax1.set_title('Feature Ablation Study Results', 
                     fontsize=14, fontweight='bold', pad=20)
        ax1.axvline(x=f1_scores[0], color='gray', linestyle='--', alpha=0.5)
        ax1.grid(axis='x', alpha=0.3)
        
        # Number of features
        ax2.barh(range(len(experiments)), num_features, color=colors, alpha=0.7)
        ax2.set_yticks(range(len(experiments)))
        ax2.set_yticklabels(labels)
        ax2.set_xlabel('Number of Features', fontsize=12, fontweight='bold')
        ax2.set_title('Features Used', fontsize=14, fontweight='bold', pad=20)
        ax2.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        save_path = 'experiments/ablation_results.png'
        os.makedirs('experiments', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nSaved ablation plot to {save_path}")
        plt.close()
    
    def save_results(self):
        """Save results to JSON."""
        output_path = 'experiments/ablation_results.json'
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to {output_path}")
    
    def generate_insights(self):
        """Generate key insights from ablation study."""
        print("\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)
        
        baseline = self.results['all']['f1_mean']
        
        # Feature group importance
        print("\n1. Feature Group Impact (F1 drop when removed):")
        for group in ['text', 'visual', 'structural']:
            drop = self.results[f'without_{group}']['f1_drop']
            drop_pct = self.results[f'without_{group}']['f1_drop_pct']
            print(f"   - {group.capitalize()}: {drop:.4f} ({drop_pct:.1f}%)")
        
        # Most important group
        drops = {
            'text': self.results['without_text']['f1_drop'],
            'visual': self.results['without_visual']['f1_drop'],
            'structural': self.results['without_structural']['f1_drop']
        }
        most_important = max(drops.items(), key=lambda x: x[1])
        print(f"\n2. Most Important Group: {most_important[0].capitalize()} "
              f"({most_important[1]:.4f} drop)")
        
        # Top features performance
        print("\n3. Feature Reduction:")
        for k in [10, 20, 30]:
            f1 = self.results[f'top_{k}']['f1_mean']
            drop = self.results[f'top_{k}']['f1_drop']
            retention = (1 - drop/baseline) * 100
            print(f"   - Top {k}: {f1:.4f} ({retention:.1f}% performance retained)")
        
        # Group sufficiency
        print("\n4. Single Group Performance:")
        for group in ['text', 'visual', 'structural']:
            f1 = self.results[f'only_{group}']['f1_mean']
            coverage = f1 / baseline * 100
            print(f"   - Only {group.capitalize()}: {f1:.4f} "
                  f"({coverage:.1f}% of baseline)")
    
    def run_full_ablation(self):
        """Run complete ablation pipeline."""
        print("="*80)
        print("FEATURE ABLATION PIPELINE")
        print("="*80)
        
        self.load_data()
        self.ablation_study()
        self.plot_ablation_results()
        self.save_results()
        self.generate_insights()
        
        print("\n" + "="*80)
        print("ABLATION COMPLETE")
        print("="*80)


def main():
    ablation = FeatureAblation()
    ablation.run_full_ablation()


if __name__ == '__main__':
    main()
