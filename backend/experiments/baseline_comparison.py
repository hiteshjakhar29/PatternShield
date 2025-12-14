"""
Baseline Comparison Experiments
Compare different model variants with statistical significance testing.
"""

import json
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from scipy.stats import chi2
import sys
import os
from typing import Dict, List

# Set random seed
np.random.seed(42)

# Import detector from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ml_detector import DarkPatternDetector


class BaselineComparison:
    """Compare multiple model variants on the same test set."""

    def __init__(self, test_data_path: str):
        """Initialize with test data."""
        self.test_data_path = test_data_path
        self.load_test_data()

        self.classes = [
            "Urgency/Scarcity",
            "Confirmshaming",
            "Obstruction",
            "Visual Interference",
            "No Pattern",
        ]

        # Store predictions for each model
        self.model_predictions = {}
        self.ground_truths = []

    def load_test_data(self):
        """Load test dataset."""
        with open(self.test_data_path, "r") as f:
            data = json.load(f)
        self.test_examples = data["examples"]
        print(f"Loaded {len(self.test_examples)} test examples\n")

    def run_model_variant(
        self, model_name: str, use_sentiment: bool = True, use_enhanced: bool = False
    ) -> List[str]:
        """
        Run a model variant on test data.

        Args:
            model_name: Name identifier for this variant
            use_sentiment: Whether to use sentiment analysis
            use_enhanced: Whether to use enhanced features

        Returns:
            List of predictions
        """
        print(f"Running {model_name}...")
        detector = DarkPatternDetector()
        predictions = []

        for example in self.test_examples:
            result = detector.analyze_element(
                text=example["text"],
                element_type=example["element_type"],
                color=example["color"],
                use_sentiment=use_sentiment,
                use_enhanced=use_enhanced,
            )

            prediction = (
                result["primary_pattern"] if result["primary_pattern"] else "No Pattern"
            )
            predictions.append(prediction)

        self.model_predictions[model_name] = predictions

        # Store ground truths (same for all models)
        if not self.ground_truths:
            self.ground_truths = [ex["ground_truth"] for ex in self.test_examples]

        # Calculate metrics
        accuracy = accuracy_score(self.ground_truths, predictions)
        macro_f1 = f1_score(
            self.ground_truths, predictions, average="macro", zero_division=0
        )
        weighted_f1 = f1_score(
            self.ground_truths, predictions, average="weighted", zero_division=0
        )

        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Macro F1: {macro_f1:.4f}")
        print(f"  Weighted F1: {weighted_f1:.4f}\n")

        return predictions

    def mcnemar_test(self, model1_name: str, model2_name: str) -> Dict:
        """
        Perform McNemar's test for statistical significance.

        Args:
            model1_name: First model name
            model2_name: Second model name

        Returns:
            Dictionary with test results
        """
        pred1 = self.model_predictions[model1_name]
        pred2 = self.model_predictions[model2_name]

        # Create contingency table
        # [correct-correct, correct-incorrect, incorrect-correct, incorrect-incorrect]
        n00 = sum(
            1
            for i in range(len(self.ground_truths))
            if pred1[i] != self.ground_truths[i] and pred2[i] != self.ground_truths[i]
        )
        n01 = sum(
            1
            for i in range(len(self.ground_truths))
            if pred1[i] != self.ground_truths[i] and pred2[i] == self.ground_truths[i]
        )
        n10 = sum(
            1
            for i in range(len(self.ground_truths))
            if pred1[i] == self.ground_truths[i] and pred2[i] != self.ground_truths[i]
        )
        n11 = sum(
            1
            for i in range(len(self.ground_truths))
            if pred1[i] == self.ground_truths[i] and pred2[i] == self.ground_truths[i]
        )

        # McNemar's test uses the off-diagonal elements
        contingency_table = [[n11, n10], [n01, n00]]

        # Perform test with continuity correction
        if n10 + n01 > 0:
            # McNemar's test statistic with continuity correction
            statistic = ((abs(n10 - n01) - 1) ** 2) / (n10 + n01)
            # Calculate p-value using chi2 distribution with 1 df
            p_value = 1 - chi2.cdf(statistic, df=1)
            # Significant if p < 0.05
            significant = p_value < 0.05
        else:
            statistic = 0
            p_value = 1.0
            significant = False

        return {
            "contingency_table": contingency_table,
            "statistic": statistic,
            "p_value": p_value,
            "significant": significant,
            "n10": n10,  # model1 correct, model2 incorrect
            "n01": n01,  # model1 incorrect, model2 correct
        }

    def calculate_improvement(self, baseline_name: str, comparison_name: str) -> Dict:
        """Calculate improvement metrics between two models."""
        baseline_preds = self.model_predictions[baseline_name]
        comparison_preds = self.model_predictions[comparison_name]

        baseline_acc = accuracy_score(self.ground_truths, baseline_preds)
        comparison_acc = accuracy_score(self.ground_truths, comparison_preds)

        baseline_f1 = f1_score(
            self.ground_truths, baseline_preds, average="macro", zero_division=0
        )
        comparison_f1 = f1_score(
            self.ground_truths, comparison_preds, average="macro", zero_division=0
        )

        # Calculate improvements
        acc_improvement = (
            (comparison_acc - baseline_acc) / baseline_acc * 100
            if baseline_acc > 0
            else 0
        )
        f1_improvement = (
            (comparison_f1 - baseline_f1) / baseline_f1 * 100 if baseline_f1 > 0 else 0
        )

        return {
            "baseline_accuracy": baseline_acc,
            "comparison_accuracy": comparison_acc,
            "accuracy_improvement_pct": acc_improvement,
            "baseline_f1": baseline_f1,
            "comparison_f1": comparison_f1,
            "f1_improvement_pct": f1_improvement,
        }

    def generate_comparison_report(self, output_path: str):
        """Generate comprehensive comparison report in Markdown."""
        report = []

        report.append("# Baseline Comparison Report")
        report.append("## PatternShield Dark Pattern Detection Models\n")
        report.append("---\n")

        # Model descriptions
        report.append("## Model Variants\n")
        report.append("### Model A: Rule-Based Only")
        report.append("- Uses only keyword and pattern matching")
        report.append("- No sentiment analysis")
        report.append("- Baseline approach\n")

        report.append("### Model B: Rule-Based + Sentiment")
        report.append("- Keyword and pattern matching")
        report.append("- TextBlob sentiment analysis")
        report.append("- Sentiment-adjusted confidence scores")
        report.append("- **Current production model**\n")

        report.append("### Model C: Rule-Based + Sentiment + Enhanced")
        report.append("- All features from Model B")
        report.append("- Color-based detection adjustments")
        report.append("- Text length-based heuristics")
        report.append("- Advanced feature engineering\n")

        report.append("---\n")

        # Overall comparison table
        report.append("## Overall Performance Comparison\n")
        report.append("| Model | Accuracy | Macro F1 | Weighted F1 |")
        report.append("|-------|----------|----------|-------------|")

        for model_name in ["Model A", "Model B", "Model C"]:
            preds = self.model_predictions[model_name]
            acc = accuracy_score(self.ground_truths, preds)
            macro_f1 = f1_score(
                self.ground_truths, preds, average="macro", zero_division=0
            )
            weighted_f1 = f1_score(
                self.ground_truths, preds, average="weighted", zero_division=0
            )

            report.append(
                f"| {model_name} | {acc:.4f} | {macro_f1:.4f} | {weighted_f1:.4f} |"
            )

        report.append("\n---\n")

        # Improvement analysis
        report.append("## Improvement Analysis\n")

        # B vs A
        report.append("### Model B vs Model A (Adding Sentiment Analysis)\n")
        improvement_ba = self.calculate_improvement("Model A", "Model B")
        report.append(
            f"- **Accuracy Improvement**: {improvement_ba['accuracy_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_ba['baseline_accuracy']:.4f}")
        report.append(
            f"  - With Sentiment: {improvement_ba['comparison_accuracy']:.4f}"
        )
        report.append(
            f"- **F1 Improvement**: {improvement_ba['f1_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_ba['baseline_f1']:.4f}")
        report.append(f"  - With Sentiment: {improvement_ba['comparison_f1']:.4f}\n")

        # Statistical significance
        mcnemar_ba = self.mcnemar_test("Model A", "Model B")
        report.append(f"**Statistical Significance (McNemar's Test)**:")
        report.append(f"- Test Statistic: {mcnemar_ba['statistic']:.4f}")
        report.append(f"- P-value: {mcnemar_ba['p_value']:.4f}")
        report.append(
            f"- Significant at α=0.05: {'Yes ✓' if mcnemar_ba['significant'] else 'No ✗'}"
        )
        report.append(f"- Model B correct where A failed: {mcnemar_ba['n01']} cases")
        report.append(f"- Model A correct where B failed: {mcnemar_ba['n10']} cases\n")

        # C vs B
        report.append("### Model C vs Model B (Adding Enhanced Features)\n")
        improvement_cb = self.calculate_improvement("Model B", "Model C")
        report.append(
            f"- **Accuracy Improvement**: {improvement_cb['accuracy_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_cb['baseline_accuracy']:.4f}")
        report.append(f"  - With Enhanced: {improvement_cb['comparison_accuracy']:.4f}")
        report.append(
            f"- **F1 Improvement**: {improvement_cb['f1_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_cb['baseline_f1']:.4f}")
        report.append(f"  - With Enhanced: {improvement_cb['comparison_f1']:.4f}\n")

        mcnemar_cb = self.mcnemar_test("Model B", "Model C")
        report.append(f"**Statistical Significance (McNemar's Test)**:")
        report.append(f"- Test Statistic: {mcnemar_cb['statistic']:.4f}")
        report.append(f"- P-value: {mcnemar_cb['p_value']:.4f}")
        report.append(
            f"- Significant at α=0.05: {'Yes ✓' if mcnemar_cb['significant'] else 'No ✗'}"
        )
        report.append(f"- Model C correct where B failed: {mcnemar_cb['n01']} cases")
        report.append(f"- Model B correct where C failed: {mcnemar_cb['n10']} cases\n")

        # C vs A
        report.append("### Model C vs Model A (Complete Enhancement)\n")
        improvement_ca = self.calculate_improvement("Model A", "Model C")
        report.append(
            f"- **Accuracy Improvement**: {improvement_ca['accuracy_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_ca['baseline_accuracy']:.4f}")
        report.append(
            f"  - Fully Enhanced: {improvement_ca['comparison_accuracy']:.4f}"
        )
        report.append(
            f"- **F1 Improvement**: {improvement_ca['f1_improvement_pct']:+.2f}%"
        )
        report.append(f"  - Baseline: {improvement_ca['baseline_f1']:.4f}")
        report.append(f"  - Fully Enhanced: {improvement_ca['comparison_f1']:.4f}\n")

        mcnemar_ca = self.mcnemar_test("Model A", "Model C")
        report.append(f"**Statistical Significance (McNemar's Test)**:")
        report.append(f"- Test Statistic: {mcnemar_ca['statistic']:.4f}")
        report.append(f"- P-value: {mcnemar_ca['p_value']:.4f}")
        report.append(
            f"- Significant at α=0.05: {'Yes ✓' if mcnemar_ca['significant'] else 'No ✗'}"
        )
        report.append(f"- Model C correct where A failed: {mcnemar_ca['n01']} cases")
        report.append(f"- Model A correct where C failed: {mcnemar_ca['n10']} cases\n")

        report.append("---\n")

        # Key insights
        report.append("## Key Insights\n")

        # Determine which model performs best
        accuracies = {
            name: accuracy_score(self.ground_truths, preds)
            for name, preds in self.model_predictions.items()
        }
        best_model = max(accuracies.items(), key=lambda x: x[1])[0]

        report.append(f"1. **Best Overall Model**: {best_model}")
        report.append(
            f"   - Achieved {accuracies[best_model]:.4f} accuracy on test set\n"
        )

        report.append("2. **Feature Impact**:")
        if improvement_ba["accuracy_improvement_pct"] > 0:
            report.append(
                f"   - Sentiment analysis provided {improvement_ba['accuracy_improvement_pct']:.2f}% accuracy boost"
            )
        if improvement_cb["accuracy_improvement_pct"] > 0:
            report.append(
                f"   - Enhanced features provided additional {improvement_cb['accuracy_improvement_pct']:.2f}% improvement"
            )
        report.append("")

        report.append("3. **Statistical Validity**:")
        if mcnemar_ca["significant"]:
            report.append(
                "   - Full enhancement shows statistically significant improvement over baseline"
            )
        else:
            report.append(
                "   - Improvements may not be statistically significant (small sample or marginal gains)"
            )
        report.append("")

        report.append("4. **Recommendations**:")
        if improvement_cb["accuracy_improvement_pct"] > 1:
            report.append(
                "   - Deploy Model C (enhanced features) for best performance"
            )
        elif improvement_ba["accuracy_improvement_pct"] > 1:
            report.append(
                "   - Model B (with sentiment) offers good balance of performance and complexity"
            )
        else:
            report.append(
                "   - Continue with baseline; focus on data collection and feature engineering"
            )
        report.append("")

        report.append("---\n")
        report.append("## Methodology\n")
        report.append(f"- **Test Set Size**: {len(self.test_examples)} examples")
        report.append("- **Evaluation Metrics**: Accuracy, Macro F1, Weighted F1")
        report.append("- **Statistical Test**: McNemar's Test (α = 0.05)")
        report.append("- **Random Seed**: 42 (for reproducibility)")
        report.append("\n---\n")
        report.append("*Report generated automatically by baseline_comparison.py*")

        # Write report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"Comparison report saved to {output_path}")

    def run_full_comparison(self, output_dir: str):
        """Run complete baseline comparison."""
        print("=" * 80)
        print("BASELINE COMPARISON EXPERIMENTS")
        print("=" * 80)
        print()

        # Run all three model variants
        self.run_model_variant("Model A", use_sentiment=False, use_enhanced=False)
        self.run_model_variant("Model B", use_sentiment=True, use_enhanced=False)
        self.run_model_variant("Model C", use_sentiment=True, use_enhanced=True)

        # Generate report
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "comparison_report.md")
        self.generate_comparison_report(report_path)

        print("\n" + "=" * 80)
        print("COMPARISON COMPLETE")
        print("=" * 80)
        print(f"\nGenerated: {report_path}")


def main():
    """Main comparison function."""
    # Use relative paths from backend directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    test_data_path = os.path.join(backend_dir, "data/test_dataset.json")
    output_dir = current_dir

    comparison = BaselineComparison(test_data_path)
    comparison.run_full_comparison(output_dir)


if __name__ == "__main__":
    main()
