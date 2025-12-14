"""
Feature Selection Methods
RFE, Mutual Information, Correlation-based, L1 regularization.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFE, mutual_info_classif, SelectKBest
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from typing import Dict, List, Tuple
import os

from feature_extraction import FeatureExtractor

np.random.seed(42)


class FeatureSelector:
    """Feature selection methods and comparison."""

    def __init__(self):
        self.extractor = FeatureExtractor()
        self.feature_names = []
        self.X = None
        self.y = None
        self.results = {}

    def load_data(self, data_path="data/training_dataset.json"):
        """Load and prepare data."""
        print(f"Loading data from {data_path}...")

        with open(data_path, "r") as f:
            data = json.load(f)

        # Use train + validation
        all_examples = data["train"] + data["validation"]
        texts = [ex["text"] for ex in all_examples]

        # Fit TF-IDF
        self.extractor.fit_tfidf(texts)

        # Extract features
        feature_dicts = []
        labels = []

        label_map = {
            "Urgency/Scarcity": 0,
            "Confirmshaming": 1,
            "Obstruction": 2,
            "Visual Interference": 3,
            "Sneaking": 4,
            "No Pattern": 5,
        }

        for ex in all_examples:
            features = self.extractor.extract_features(
                ex["text"],
                ex.get("element_type", "div"),
                ex.get("color", "#000000"),
                include_tfidf=False,
            )
            feature_dicts.append(features)
            labels.append(label_map[ex["label"]])

        # Convert to arrays
        self.feature_names = sorted(feature_dicts[0].keys())
        self.X = np.array(
            [[fd[name] for name in self.feature_names] for fd in feature_dicts]
        )
        self.y = np.array(labels)

        print(f"Data shape: {self.X.shape}")
        return self.X, self.y

    def baseline_performance(self):
        """Measure baseline performance with all features."""
        print("\n" + "=" * 80)
        print("BASELINE PERFORMANCE (All Features)")
        print("=" * 80)

        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        scores = cross_val_score(rf, self.X, self.y, cv=5, scoring="f1_macro")

        baseline_f1 = scores.mean()
        baseline_std = scores.std()

        print(f"5-Fold CV F1: {baseline_f1:.4f} ± {baseline_std:.4f}")
        print(f"Total features: {self.X.shape[1]}")

        self.results["baseline"] = {
            "f1_mean": float(baseline_f1),
            "f1_std": float(baseline_std),
            "num_features": int(self.X.shape[1]),
            "features": self.feature_names,
        }

        return baseline_f1

    def rfe_selection(self, n_features=20):
        """Recursive Feature Elimination."""
        print("\n" + "=" * 80)
        print(f"RECURSIVE FEATURE ELIMINATION (Top {n_features})")
        print("=" * 80)

        rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)

        rfe = RFE(estimator=rf, n_features_to_select=n_features, step=5)
        rfe.fit(self.X, self.y)

        selected_features = [
            name for name, selected in zip(self.feature_names, rfe.support_) if selected
        ]
        X_selected = self.X[:, rfe.support_]

        # Evaluate
        scores = cross_val_score(rf, X_selected, self.y, cv=5, scoring="f1_macro")
        f1_mean = scores.mean()
        f1_std = scores.std()

        print(f"Selected {len(selected_features)} features")
        print(f"5-Fold CV F1: {f1_mean:.4f} ± {f1_std:.4f}")
        print(f"F1 drop: {self.results['baseline']['f1_mean'] - f1_mean:.4f}")

        self.results["rfe"] = {
            "f1_mean": float(f1_mean),
            "f1_std": float(f1_std),
            "num_features": len(selected_features),
            "features": selected_features,
            "f1_drop": float(self.results["baseline"]["f1_mean"] - f1_mean),
        }

        return selected_features

    def mutual_information_selection(self, k=20):
        """Select top k features by mutual information."""
        print("\n" + "=" * 80)
        print(f"MUTUAL INFORMATION SELECTION (Top {k})")
        print("=" * 80)

        mi_scores = mutual_info_classif(self.X, self.y, random_state=42)
        top_indices = np.argsort(mi_scores)[::-1][:k]

        selected_features = [self.feature_names[i] for i in top_indices]
        X_selected = self.X[:, top_indices]

        # Evaluate
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        scores = cross_val_score(rf, X_selected, self.y, cv=5, scoring="f1_macro")
        f1_mean = scores.mean()
        f1_std = scores.std()

        print(f"Selected {len(selected_features)} features")
        print(f"5-Fold CV F1: {f1_mean:.4f} ± {f1_std:.4f}")
        print(f"F1 drop: {self.results['baseline']['f1_mean'] - f1_mean:.4f}")

        self.results["mutual_info"] = {
            "f1_mean": float(f1_mean),
            "f1_std": float(f1_std),
            "num_features": len(selected_features),
            "features": selected_features,
            "f1_drop": float(self.results["baseline"]["f1_mean"] - f1_mean),
        }

        return selected_features

    def correlation_based_selection(self, threshold=0.9):
        """Remove highly correlated features."""
        print("\n" + "=" * 80)
        print(f"CORRELATION-BASED SELECTION (threshold={threshold})")
        print("=" * 80)

        # Compute correlation matrix
        corr_matrix = np.corrcoef(self.X.T)

        # Find correlated pairs
        to_remove = set()
        for i in range(len(corr_matrix)):
            for j in range(i + 1, len(corr_matrix)):
                if abs(corr_matrix[i, j]) > threshold:
                    # Remove feature with lower variance
                    if np.var(self.X[:, i]) < np.var(self.X[:, j]):
                        to_remove.add(i)
                    else:
                        to_remove.add(j)

        # Select features
        keep_indices = [i for i in range(len(self.feature_names)) if i not in to_remove]
        selected_features = [self.feature_names[i] for i in keep_indices]
        X_selected = self.X[:, keep_indices]

        # Evaluate
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        scores = cross_val_score(rf, X_selected, self.y, cv=5, scoring="f1_macro")
        f1_mean = scores.mean()
        f1_std = scores.std()

        print(f"Removed {len(to_remove)} highly correlated features")
        print(f"Selected {len(selected_features)} features")
        print(f"5-Fold CV F1: {f1_mean:.4f} ± {f1_std:.4f}")
        print(f"F1 drop: {self.results['baseline']['f1_mean'] - f1_mean:.4f}")

        self.results["correlation"] = {
            "f1_mean": float(f1_mean),
            "f1_std": float(f1_std),
            "num_features": len(selected_features),
            "features": selected_features,
            "removed": int(len(to_remove)),
            "f1_drop": float(self.results["baseline"]["f1_mean"] - f1_mean),
        }

        return selected_features

    def l1_selection(self, C=0.1):
        """L1 regularization feature selection."""
        print("\n" + "=" * 80)
        print(f"L1 REGULARIZATION SELECTION (C={C})")
        print("=" * 80)

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        # L1 logistic regression
        lr = LogisticRegression(
            penalty="l1", C=C, solver="liblinear", random_state=42, max_iter=1000
        )
        lr.fit(X_scaled, self.y)

        # Select non-zero coefficients
        non_zero = np.any(lr.coef_ != 0, axis=0)
        selected_features = [
            name for name, nz in zip(self.feature_names, non_zero) if nz
        ]
        X_selected = self.X[:, non_zero]

        # Evaluate
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        scores = cross_val_score(rf, X_selected, self.y, cv=5, scoring="f1_macro")
        f1_mean = scores.mean()
        f1_std = scores.std()

        print(f"Selected {len(selected_features)} features")
        print(f"5-Fold CV F1: {f1_mean:.4f} ± {f1_std:.4f}")
        print(f"F1 drop: {self.results['baseline']['f1_mean'] - f1_mean:.4f}")

        self.results["l1"] = {
            "f1_mean": float(f1_mean),
            "f1_std": float(f1_std),
            "num_features": len(selected_features),
            "features": selected_features,
            "f1_drop": float(self.results["baseline"]["f1_mean"] - f1_mean),
        }

        return selected_features

    def plot_comparison(self):
        """Plot comparison of selection methods."""
        methods = ["baseline", "rfe", "mutual_info", "correlation", "l1"]
        method_names = ["Baseline\n(All)", "RFE", "Mutual\nInfo", "Correlation", "L1"]

        f1_scores = [self.results[m]["f1_mean"] for m in methods]
        f1_stds = [self.results[m]["f1_std"] for m in methods]
        num_features = [self.results[m]["num_features"] for m in methods]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # F1 scores
        bars1 = ax1.bar(range(len(methods)), f1_scores, yerr=f1_stds, capsize=5)
        ax1.set_xticks(range(len(methods)))
        ax1.set_xticklabels(method_names)
        ax1.set_ylabel("F1 Score (5-Fold CV)", fontsize=12, fontweight="bold")
        ax1.set_title("Feature Selection Performance", fontsize=14, fontweight="bold")
        ax1.grid(axis="y", alpha=0.3)

        # Color baseline differently
        bars1[0].set_color("green")
        bars1[0].set_alpha(0.7)

        # Number of features
        bars2 = ax2.bar(range(len(methods)), num_features)
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(method_names)
        ax2.set_ylabel("Number of Features", fontsize=12, fontweight="bold")
        ax2.set_title("Features Selected", fontsize=14, fontweight="bold")
        ax2.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            "analysis_plots/feature_selection_comparison.png",
            dpi=300,
            bbox_inches="tight",
        )
        print(
            "\nSaved comparison plot to analysis_plots/feature_selection_comparison.png"
        )
        plt.close()

    def run_all_methods(self):
        """Run all feature selection methods."""
        print("=" * 80)
        print("FEATURE SELECTION COMPARISON")
        print("=" * 80)

        # Baseline
        self.baseline_performance()

        # Methods
        self.rfe_selection(n_features=20)
        self.mutual_information_selection(k=20)
        self.correlation_based_selection(threshold=0.9)
        self.l1_selection(C=0.1)

        # Plot comparison
        self.plot_comparison()

        # Save results
        results_path = "FEATURE_SELECTION_RESULTS.md"
        self.generate_markdown_report(results_path)

        print("\n" + "=" * 80)
        print("FEATURE SELECTION COMPLETE")
        print("=" * 80)

        return self.results

    def generate_markdown_report(self, output_path):
        """Generate markdown report."""
        report = []

        report.append("# Feature Selection Results\n")
        report.append("## Comparison of Feature Selection Methods\n")
        report.append("---\n")

        # Summary table
        report.append("## Performance Summary\n")
        report.append("| Method | F1 Score | Std Dev | Num Features | F1 Drop |")
        report.append("|--------|----------|---------|--------------|---------|")

        for method, name in [
            ("baseline", "Baseline (All)"),
            ("rfe", "RFE"),
            ("mutual_info", "Mutual Information"),
            ("correlation", "Correlation-based"),
            ("l1", "L1 Regularization"),
        ]:
            r = self.results[method]
            f1_drop = r.get("f1_drop", 0.0)
            report.append(
                f"| {name} | {r['f1_mean']:.4f} | {r['f1_std']:.4f} | "
                f"{r['num_features']} | {f1_drop:.4f} |"
            )

        report.append("\n---\n")

        # Key findings
        report.append("## Key Findings\n")

        best_method = max(
            [(k, v) for k, v in self.results.items() if k != "baseline"],
            key=lambda x: x[1]["f1_mean"],
        )

        report.append(
            f"1. **Best Method**: {best_method[0]} "
            f"(F1: {best_method[1]['f1_mean']:.4f})\n"
        )

        report.append(
            f"2. **Baseline F1**: {self.results['baseline']['f1_mean']:.4f} "
            f"with {self.results['baseline']['num_features']} features\n"
        )

        # Feature reduction
        for method in ["rfe", "mutual_info", "l1"]:
            reduction = (
                1
                - self.results[method]["num_features"]
                / self.results["baseline"]["num_features"]
            ) * 100
            report.append(
                f"3. **{method}**: Reduced features by {reduction:.1f}% "
                f"with {self.results[method]['f1_drop']:.4f} F1 drop\n"
            )

        report.append("\n---\n")
        report.append("## Method Details\n")

        report.append("### Recursive Feature Elimination (RFE)\n")
        report.append("- Iteratively removes least important features\n")
        report.append("- Uses Random Forest for ranking\n")
        report.append(f"- Selected: {self.results['rfe']['num_features']} features\n")

        report.append("\n### Mutual Information\n")
        report.append("- Measures dependency between features and target\n")
        report.append("- Selects top k most informative features\n")
        report.append(
            f"- Selected: {self.results['mutual_info']['num_features']} features\n"
        )

        report.append("\n### Correlation-based\n")
        report.append("- Removes highly correlated redundant features\n")
        report.append(f"- Threshold: 0.9\n")
        report.append(
            f"- Removed: {self.results['correlation'].get('removed', 0)} features\n"
        )

        report.append("\n### L1 Regularization\n")
        report.append("- Sparse logistic regression\n")
        report.append("- Automatically selects non-zero coefficients\n")
        report.append(f"- Selected: {self.results['l1']['num_features']} features\n")

        report.append("\n---\n")
        report.append("## Recommendations\n")

        if best_method[1]["f1_drop"] < 0.01:
            report.append("- Feature selection maintains performance\n")
            report.append(f"- Use **{best_method[0]}** for reduced model complexity\n")
        else:
            report.append("- Baseline performs best\n")
            report.append("- All features contribute to performance\n")

        report.append("\n---\n")
        report.append("*Report generated by feature_selection.py*\n")

        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"Report saved to {output_path}")


def main():
    selector = FeatureSelector()
    selector.load_data()
    selector.run_all_methods()


if __name__ == "__main__":
    main()
