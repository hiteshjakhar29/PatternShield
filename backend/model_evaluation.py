"""
Model Evaluation Script for PatternShield
Comprehensive evaluation with metrics, visualizations, and error analysis.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
)
from sklearn.preprocessing import label_binarize
from collections import defaultdict
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))
from ml_detector import DarkPatternDetector


# Set random seed for reproducibility
np.random.seed(42)

# Configure matplotlib for professional styling
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")


class ModelEvaluator:
    """Comprehensive model evaluation framework."""

    def __init__(self, test_data_path: str):
        """Initialize evaluator with test dataset."""
        self.test_data_path = test_data_path
        self.detector = DarkPatternDetector()
        self.load_test_data()

        # All possible classes including "No Pattern"
        self.classes = [
            "Urgency/Scarcity",
            "Confirmshaming",
            "Obstruction",
            "Visual Interference",
            "No Pattern",
        ]

        self.results = None
        self.predictions = []
        self.ground_truths = []
        self.errors = {"false_positives": [], "false_negatives": []}

    def load_test_data(self):
        """Load test dataset from JSON."""
        print(f"Loading test data from {self.test_data_path}...")
        with open(self.test_data_path, "r") as f:
            data = json.load(f)

        self.test_examples = data["examples"]
        self.metadata = data.get("metadata", {})
        print(f"Loaded {len(self.test_examples)} test examples")
        print(f"Categories: {self.metadata.get('categories', {})}")

    def run_predictions(self):
        """Run model predictions on all test examples."""
        print("\nRunning predictions...")

        for example in self.test_examples:
            result = self.detector.analyze_element(
                text=example["text"],
                element_type=example["element_type"],
                color=example["color"],
                use_sentiment=True,
                use_enhanced=False,
            )

            # Get prediction
            prediction = (
                result["primary_pattern"] if result["primary_pattern"] else "No Pattern"
            )
            ground_truth = example["ground_truth"]

            self.predictions.append(prediction)
            self.ground_truths.append(ground_truth)

            # Track errors
            if prediction != ground_truth:
                error_info = {
                    "id": example["id"],
                    "text": example["text"],
                    "predicted": prediction,
                    "ground_truth": ground_truth,
                    "confidence": (
                        result["confidence_scores"].get(prediction, 0)
                        if prediction != "No Pattern"
                        else 0
                    ),
                    "difficulty": example.get("difficulty", "unknown"),
                    "notes": example.get("notes", ""),
                }

                if prediction == "No Pattern":
                    self.errors["false_negatives"].append(error_info)
                elif ground_truth == "No Pattern":
                    self.errors["false_positives"].append(error_info)
                else:
                    # Misclassification between pattern types
                    self.errors["false_negatives"].append(error_info)

        print(f"Predictions complete: {len(self.predictions)} examples processed")

    def calculate_metrics(self):
        """Calculate comprehensive evaluation metrics."""
        print("\nCalculating metrics...")

        self.results = {"overall": {}, "per_class": {}, "confusion_matrix": None}

        # Overall metrics
        self.results["overall"]["accuracy"] = accuracy_score(
            self.ground_truths, self.predictions
        )

        self.results["overall"]["macro_f1"] = f1_score(
            self.ground_truths, self.predictions, average="macro", zero_division=0
        )

        self.results["overall"]["weighted_f1"] = f1_score(
            self.ground_truths, self.predictions, average="weighted", zero_division=0
        )

        # Per-class metrics
        for cls in self.classes:
            # Binary classification for each class
            y_true_binary = [1 if gt == cls else 0 for gt in self.ground_truths]
            y_pred_binary = [1 if pred == cls else 0 for pred in self.predictions]

            precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
            recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
            f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)

            # Support (number of actual instances)
            support = sum(y_true_binary)

            self.results["per_class"][cls] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
            }

        # Confusion matrix
        self.results["confusion_matrix"] = confusion_matrix(
            self.ground_truths, self.predictions, labels=self.classes
        )

        print("Metrics calculated successfully")

    def generate_confusion_matrix_plot(self, save_path: str):
        """Generate and save confusion matrix heatmap."""
        print(f"\nGenerating confusion matrix plot...")

        cm = self.results["confusion_matrix"]

        plt.figure(figsize=(12, 10))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.classes,
            yticklabels=self.classes,
            cbar_kws={"label": "Count"},
            square=True,
            linewidths=0.5,
        )

        plt.title(
            "Confusion Matrix - Dark Pattern Detection",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )
        plt.ylabel("True Label", fontsize=12, fontweight="bold")
        plt.xlabel("Predicted Label", fontsize=12, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()

        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Confusion matrix saved to {save_path}")
        plt.close()

    def generate_roc_curves(self, save_path: str):
        """Generate ROC curves for each class."""
        print(f"\nGenerating ROC curves...")

        # Binarize the labels
        y_true_bin = label_binarize(self.ground_truths, classes=self.classes)
        y_pred_bin = label_binarize(self.predictions, classes=self.classes)

        plt.figure(figsize=(14, 10))

        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

        for i, (cls, color) in enumerate(zip(self.classes, colors)):
            # Calculate ROC curve and AUC
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred_bin[:, i])
            roc_auc = auc(fpr, tpr)

            plt.plot(
                fpr, tpr, color=color, lw=2.5, label=f"{cls} (AUC = {roc_auc:.3f})"
            )

        # Plot diagonal
        plt.plot([0, 1], [0, 1], "k--", lw=1.5, label="Random Classifier")

        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate", fontsize=12, fontweight="bold")
        plt.ylabel("True Positive Rate", fontsize=12, fontweight="bold")
        plt.title(
            "ROC Curves - Per-Class Performance", fontsize=16, fontweight="bold", pad=20
        )
        plt.legend(loc="lower right", fontsize=10, framealpha=0.9)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"ROC curves saved to {save_path}")
        plt.close()

    def analyze_errors(self):
        """Perform detailed error analysis."""
        print("\n" + "=" * 80)
        print("ERROR ANALYSIS")
        print("=" * 80)

        # Sort errors by confidence (for false positives) or by difficulty
        self.errors["false_positives"].sort(key=lambda x: x["confidence"], reverse=True)
        self.errors["false_negatives"].sort(
            key=lambda x: x["difficulty"] == "hard", reverse=True
        )

        # Top 5 False Positives
        print("\n" + "-" * 80)
        print("TOP 5 FALSE POSITIVES (Detected pattern when none exists)")
        print("-" * 80)

        fp_count = 0
        for i, error in enumerate(self.errors["false_positives"][:5], 1):
            if error["ground_truth"] == "No Pattern":
                fp_count += 1
                print(
                    f"\n{i}. ID: {error['id']} | Confidence: {error['confidence']:.3f}"
                )
                print(f"   Text: \"{error['text']}\"")
                print(
                    f"   Predicted: {error['predicted']} | Ground Truth: {error['ground_truth']}"
                )
                print(f"   Difficulty: {error['difficulty']}")
                print(f"   Explanation: {error['notes']}")
                print(
                    f"   Analysis: Model over-triggered on keywords without considering context"
                )

        if fp_count == 0:
            print("\n✓ No false positives on 'No Pattern' examples!")

        # Top 5 False Negatives
        print("\n" + "-" * 80)
        print("TOP 5 FALSE NEGATIVES (Missed detecting actual patterns)")
        print("-" * 80)

        fn_shown = 0
        for i, error in enumerate(self.errors["false_negatives"]):
            if error["predicted"] == "No Pattern" and fn_shown < 5:
                fn_shown += 1
                print(
                    f"\n{fn_shown}. ID: {error['id']} | Difficulty: {error['difficulty']}"
                )
                print(f"   Text: \"{error['text']}\"")
                print(
                    f"   Predicted: {error['predicted']} | Ground Truth: {error['ground_truth']}"
                )
                print(f"   Explanation: {error['notes']}")
                print(f"   Analysis: Pattern too subtle or requires domain knowledge")

        # Misclassification between pattern types
        print("\n" + "-" * 80)
        print("PATTERN MISCLASSIFICATION (Wrong pattern type detected)")
        print("-" * 80)

        misclass_count = 0
        for error in self.errors["false_negatives"]:
            if (
                error["predicted"] != "No Pattern"
                and error["ground_truth"] != "No Pattern"
            ):
                if misclass_count < 5:
                    misclass_count += 1
                    print(f"\n{misclass_count}. ID: {error['id']}")
                    print(f"   Text: \"{error['text']}\"")
                    print(
                        f"   Predicted: {error['predicted']} | Ground Truth: {error['ground_truth']}"
                    )
                    print(f"   Analysis: Overlapping features between pattern types")

        if misclass_count == 0:
            print("\n✓ No misclassifications between pattern types!")

        # Error statistics
        print("\n" + "=" * 80)
        print("ERROR STATISTICS")
        print("=" * 80)
        total_errors = len(
            [
                e
                for e in self.errors["false_positives"]
                if e["ground_truth"] == "No Pattern"
            ]
        )
        total_errors += len(
            [
                e
                for e in self.errors["false_negatives"]
                if e["predicted"] == "No Pattern"
            ]
        )

        print(f"\nTotal Errors: {total_errors}/{len(self.test_examples)}")
        print(
            f"False Positives (No Pattern misclassified): "
            f"{len([e for e in self.errors['false_positives'] if e['ground_truth'] == 'No Pattern'])}"
        )
        print(
            f"False Negatives (Pattern missed): "
            f"{len([e for e in self.errors['false_negatives'] if e['predicted'] == 'No Pattern'])}"
        )
        print(f"Pattern Misclassifications: {misclass_count}")

    def print_comprehensive_report(self):
        """Print comprehensive evaluation report."""
        print("\n" + "=" * 80)
        print("MODEL EVALUATION REPORT - PatternShield Dark Pattern Detector")
        print("=" * 80)

        # Overall metrics
        print("\n" + "-" * 80)
        print("OVERALL METRICS")
        print("-" * 80)
        print(f"Accuracy:     {self.results['overall']['accuracy']:.4f}")
        print(f"Macro F1:     {self.results['overall']['macro_f1']:.4f}")
        print(f"Weighted F1:  {self.results['overall']['weighted_f1']:.4f}")

        # Per-class metrics
        print("\n" + "-" * 80)
        print("PER-CLASS METRICS")
        print("-" * 80)
        print(
            f"{'Class':<25} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}"
        )
        print("-" * 80)

        for cls in self.classes:
            metrics = self.results["per_class"][cls]
            print(
                f"{cls:<25} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} "
                f"{metrics['f1']:<12.4f} {metrics['support']:<10}"
            )

        # Category analysis
        print("\n" + "-" * 80)
        print("PERFORMANCE BY DIFFICULTY")
        print("-" * 80)

        difficulty_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for i, example in enumerate(self.test_examples):
            difficulty = example.get("difficulty", "unknown")
            difficulty_stats[difficulty]["total"] += 1
            if self.predictions[i] == self.ground_truths[i]:
                difficulty_stats[difficulty]["correct"] += 1

        for difficulty in ["easy", "medium", "hard"]:
            if difficulty in difficulty_stats:
                stats = difficulty_stats[difficulty]
                accuracy = (
                    stats["correct"] / stats["total"] if stats["total"] > 0 else 0
                )
                print(
                    f"{difficulty.capitalize():<15} {accuracy:.4f} ({stats['correct']}/{stats['total']})"
                )

    def save_results(self, output_path: str):
        """Save evaluation results to JSON."""
        print(f"\nSaving results to {output_path}...")

        results_dict = {
            "metadata": {
                "model": "Rule-based + Sentiment Analysis",
                "test_dataset": self.test_data_path,
                "total_examples": len(self.test_examples),
                "timestamp": "2025-11-25",
            },
            "overall_metrics": {
                "accuracy": float(self.results["overall"]["accuracy"]),
                "macro_f1": float(self.results["overall"]["macro_f1"]),
                "weighted_f1": float(self.results["overall"]["weighted_f1"]),
            },
            "per_class_metrics": {
                cls: {
                    "precision": float(metrics["precision"]),
                    "recall": float(metrics["recall"]),
                    "f1": float(metrics["f1"]),
                    "support": int(metrics["support"]),
                }
                for cls, metrics in self.results["per_class"].items()
            },
            "confusion_matrix": self.results["confusion_matrix"].tolist(),
            "class_labels": self.classes,
            "error_analysis": {
                "false_positives_count": len(
                    [
                        e
                        for e in self.errors["false_positives"]
                        if e["ground_truth"] == "No Pattern"
                    ]
                ),
                "false_negatives_count": len(
                    [
                        e
                        for e in self.errors["false_negatives"]
                        if e["predicted"] == "No Pattern"
                    ]
                ),
                "top_false_positives": self.errors["false_positives"][:5],
                "top_false_negatives": [
                    e
                    for e in self.errors["false_negatives"]
                    if e["predicted"] == "No Pattern"
                ][:5],
            },
        }

        with open(output_path, "w") as f:
            json.dump(results_dict, f, indent=2)

        print(f"Results saved successfully")

    def run_full_evaluation(self, output_dir: str):
        """Run complete evaluation pipeline."""
        print("\n" + "=" * 80)
        print("STARTING FULL EVALUATION PIPELINE")
        print("=" * 80)

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Run evaluation steps
        self.run_predictions()
        self.calculate_metrics()
        self.print_comprehensive_report()

        # Generate visualizations
        cm_path = os.path.join(output_dir, "confusion_matrix.png")
        roc_path = os.path.join(output_dir, "roc_curves.png")

        self.generate_confusion_matrix_plot(cm_path)
        self.generate_roc_curves(roc_path)

        # Error analysis
        self.analyze_errors()

        # Save results
        results_path = os.path.join(output_dir, "evaluation_results.json")
        self.save_results(results_path)

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)
        print(f"\nGenerated files:")
        print(f"  - {cm_path}")
        print(f"  - {roc_path}")
        print(f"  - {results_path}")


def main():
    """Main evaluation function."""
    # Paths
    test_data_path = "data/test_dataset.json"
    output_dir = "."

    # Run evaluation
    evaluator = ModelEvaluator(test_data_path)
    evaluator.run_full_evaluation(output_dir)


if __name__ == "__main__":
    main()
