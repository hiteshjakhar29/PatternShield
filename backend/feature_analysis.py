"""
Feature Analysis and Importance
Analyze features using Random Forest, SHAP, correlation, and t-SNE.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_classif

# Try to import SHAP (optional)
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("⚠ SHAP not installed. SHAP analysis will be skipped.")
    print("  Install with: pip install shap")

from typing import Dict, List, Tuple
import os

from feature_extraction import FeatureExtractor

# Set random seed
np.random.seed(42)

# Configure matplotlib
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    try:
        plt.style.use('seaborn-darkgrid')
    except:
        pass  # Use default style
        
sns.set_palette("husl")


class FeatureAnalyzer:
    """Analyze feature importance and relationships."""
    
    def __init__(self, output_dir='analysis_plots'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.extractor = FeatureExtractor()
        self.feature_names = []
        self.feature_matrix = None
        self.labels = None
        self.rf_model = None
        
    def load_and_extract_features(self, data_path='data/training_dataset.json'):
        """Load dataset and extract features."""
        print(f"Loading data from {data_path}...")
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # Combine train and validation for analysis
        all_examples = data['train'] + data['validation']
        
        texts = [ex['text'] for ex in all_examples]
        
        # Fit TF-IDF
        print("Fitting TF-IDF vectorizer...")
        self.extractor.fit_tfidf(texts)
        
        # Extract features
        print("Extracting features...")
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
                include_tfidf=False  # Too many features for SHAP
            )
            feature_dicts.append(features)
            labels.append(label_map[ex['label']])
        
        # Convert to matrix
        self.feature_names = sorted(feature_dicts[0].keys())
        self.feature_matrix = np.array([
            [fd[name] for name in self.feature_names]
            for fd in feature_dicts
        ])
        self.labels = np.array(labels)
        
        print(f"Feature matrix shape: {self.feature_matrix.shape}")
        print(f"Classes: {np.unique(self.labels)}")
        
        return self.feature_matrix, self.labels
    
    def train_random_forest(self):
        """Train Random Forest for feature importance."""
        print("\nTraining Random Forest...")
        
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.rf_model.fit(self.feature_matrix, self.labels)
        
        train_acc = self.rf_model.score(self.feature_matrix, self.labels)
        print(f"Training accuracy: {train_acc:.4f}")
        
        return self.rf_model
    
    def plot_feature_importance(self, top_n=20):
        """Plot feature importance from Random Forest."""
        print(f"\nPlotting top {top_n} feature importances...")
        
        importances = self.rf_model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        plt.figure(figsize=(12, 8))
        plt.barh(range(top_n), importances[indices])
        plt.yticks(range(top_n), [self.feature_names[i] for i in indices])
        plt.xlabel('Importance', fontsize=12, fontweight='bold')
        plt.ylabel('Feature', fontsize=12, fontweight='bold')
        plt.title('Top 20 Feature Importances (Random Forest)', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, 'feature_importance.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")
        plt.close()
        
        # Return top features
        top_features = [(self.feature_names[i], importances[i]) for i in indices]
        return top_features
    
    def plot_correlation_matrix(self, method='pearson'):
        """Plot feature correlation heatmap."""
        print(f"\nComputing {method} correlation matrix...")
        
        # Use subset of features to keep plot readable
        # Select top features by variance
        feature_vars = np.var(self.feature_matrix, axis=0)
        top_var_indices = np.argsort(feature_vars)[::-1][:30]
        
        feature_subset = self.feature_matrix[:, top_var_indices]
        feature_names_subset = [self.feature_names[i] for i in top_var_indices]
        
        # Compute correlation
        if method == 'pearson':
            corr_matrix = np.corrcoef(feature_subset.T)
        else:
            from scipy.stats import spearmanr
            corr_matrix, _ = spearmanr(feature_subset, axis=0)
        
        # Plot
        plt.figure(figsize=(14, 12))
        sns.heatmap(
            corr_matrix,
            xticklabels=feature_names_subset,
            yticklabels=feature_names_subset,
            cmap='RdBu_r',
            center=0,
            vmin=-1,
            vmax=1,
            square=True,
            linewidths=0.5,
            cbar_kws={'label': 'Correlation'}
        )
        plt.title(f'Feature Correlation Matrix ({method.capitalize()})', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, f'correlation_matrix_{method}.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")
        plt.close()
        
        return corr_matrix
    
    def compute_mutual_information(self):
        """Compute mutual information scores."""
        print("\nComputing mutual information scores...")
        
        mi_scores = mutual_info_classif(
            self.feature_matrix,
            self.labels,
            random_state=42
        )
        
        # Plot top features
        indices = np.argsort(mi_scores)[::-1][:20]
        
        plt.figure(figsize=(12, 8))
        plt.barh(range(20), mi_scores[indices])
        plt.yticks(range(20), [self.feature_names[i] for i in indices])
        plt.xlabel('Mutual Information Score', fontsize=12, fontweight='bold')
        plt.ylabel('Feature', fontsize=12, fontweight='bold')
        plt.title('Top 20 Features by Mutual Information', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, 'mutual_information.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")
        plt.close()
        
        return mi_scores
    
    def shap_analysis(self, num_samples=200):
        """Compute SHAP values for explainability."""
        if not HAS_SHAP:
            print("\n⊘ SHAP analysis skipped (shap not installed)")
            print("  Install with: pip install shap")
            return None
            
        print(f"\nComputing SHAP values (using {num_samples} samples)...")
        
        # Use subset of data for speed
        if len(self.feature_matrix) > num_samples:
            indices = np.random.choice(len(self.feature_matrix), num_samples, replace=False)
            X_sample = self.feature_matrix[indices]
        else:
            X_sample = self.feature_matrix
        
        # Create SHAP explainer
        explainer = shap.TreeExplainer(self.rf_model)
        shap_values = explainer.shap_values(X_sample)
        
        # Summary plot (for multiclass, shap_values is a list)
        plt.figure(figsize=(12, 8))
        
        if isinstance(shap_values, list):
            # Average SHAP values across classes
            shap_values_mean = np.mean(np.abs(shap_values), axis=0)
            shap.summary_plot(
                shap_values_mean,
                X_sample,
                feature_names=self.feature_names,
                show=False,
                max_display=20
            )
        else:
            shap.summary_plot(
                shap_values,
                X_sample,
                feature_names=self.feature_names,
                show=False,
                max_display=20
            )
        
        plt.title('SHAP Feature Importance Summary', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, 'shap_summary.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")
        plt.close()
        
        return shap_values
    
    def plot_tsne(self, perplexity=30):
        """Plot t-SNE visualization of feature space."""
        print(f"\nComputing t-SNE visualization (perplexity={perplexity})...")
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.feature_matrix)
        
        # t-SNE
        tsne = TSNE(
            n_components=2,
            perplexity=perplexity,
            random_state=42,
            n_jobs=-1
        )
        X_tsne = tsne.fit_transform(X_scaled)
        
        # Plot
        label_names = [
            'Urgency/Scarcity',
            'Confirmshaming',
            'Obstruction',
            'Visual Interference',
            'Sneaking',
            'No Pattern'
        ]
        
        plt.figure(figsize=(12, 10))
        scatter = plt.scatter(
            X_tsne[:, 0],
            X_tsne[:, 1],
            c=self.labels,
            cmap='tab10',
            alpha=0.6,
            s=50
        )
        plt.colorbar(scatter, label='Class', ticks=range(6))
        plt.clim(-0.5, 5.5)
        
        # Add legend
        handles = [plt.Line2D([0], [0], marker='o', color='w', 
                             markerfacecolor=scatter.cmap(scatter.norm(i)), 
                             markersize=10, label=label_names[i]) 
                  for i in range(6)]
        plt.legend(handles=handles, loc='best', framealpha=0.9)
        
        plt.xlabel('t-SNE Component 1', fontsize=12, fontweight='bold')
        plt.ylabel('t-SNE Component 2', fontsize=12, fontweight='bold')
        plt.title('t-SNE Visualization of Feature Space', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, 'tsne_visualization.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")
        plt.close()
        
        return X_tsne
    
    def run_full_analysis(self):
        """Run complete feature analysis pipeline."""
        print("="*80)
        print("FEATURE ANALYSIS PIPELINE")
        print("="*80)
        
        # Load and extract
        self.load_and_extract_features()
        
        # Train model
        self.train_random_forest()
        
        # Feature importance
        top_features = self.plot_feature_importance()
        
        # Correlation
        self.plot_correlation_matrix('pearson')
        
        # Mutual information
        mi_scores = self.compute_mutual_information()
        
        # SHAP analysis
        self.shap_analysis()
        
        # t-SNE
        self.plot_tsne()
        
        # Save results
        results = {
            'top_features_rf': [
                {'name': name, 'importance': float(imp)}
                for name, imp in top_features[:20]
            ],
            'mutual_information_top': [
                {
                    'name': self.feature_names[i],
                    'score': float(mi_scores[i])
                }
                for i in np.argsort(mi_scores)[::-1][:20]
            ],
            'total_features': len(self.feature_names),
            'dataset_size': len(self.labels)
        }
        
        results_path = os.path.join(self.output_dir, 'analysis_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nGenerated plots in: {self.output_dir}/")
        print(f"Results saved to: {results_path}")
        
        print("\nTop 10 Features (Random Forest):")
        for i, (name, imp) in enumerate(top_features[:10], 1):
            print(f"  {i}. {name}: {imp:.4f}")


def main():
    analyzer = FeatureAnalyzer()
    analyzer.run_full_analysis()


if __name__ == '__main__':
    main()
