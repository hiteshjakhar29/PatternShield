"""
Model Comparison Benchmark
Compare rule-based, transformer, and ensemble models on performance and speed.
"""

import json
import time
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
)
from typing import Dict, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ml_detector import DarkPatternDetector
from transformer_detector import TransformerDetector, EnsembleDetector


class ModelBenchmark:
    """Benchmark multiple detection models."""

    def __init__(self, test_data_path="data/training_dataset.json"):
        self.test_data_path = test_data_path
        self.load_test_data()

        # Initialize models
        print("Initializing models...")
        self.rule_detector = DarkPatternDetector()
        self.transformer_detector = TransformerDetector()
        self.ensemble_detector = EnsembleDetector()

        self.label_map = {
            "Urgency/Scarcity": "Urgency/Scarcity",
            "Confirmshaming": "Confirmshaming",
            "Obstruction": "Obstruction",
            "Visual Interference": "Visual Interference",
            "Sneaking": "Sneaking",
            "No Pattern": "No Pattern",
        }

    def load_test_data(self):
        """Load test dataset."""
        print(f"Loading test data from {self.test_data_path}...")
        with open(self.test_data_path, "r") as f:
            data = json.load(f)

        self.test_texts = [ex["text"] for ex in data["test"]]
        self.test_labels = [ex["label"] for ex in data["test"]]
        print(f"Loaded {len(self.test_texts)} test examples")

    def benchmark_rule_based(self) -> Dict:
        """Benchmark rule-based detector."""
        print("\n" + "=" * 80)
        print("Benchmarking Rule-Based Detector")
        print("=" * 80)

        predictions = []
        inference_times = []

        for text in self.test_texts:
            start_time = time.time()
            result = self.rule_detector.analyze_element(text)
            inference_time = time.time() - start_time

            pred_label = (
                result["primary_pattern"] if result["primary_pattern"] else "No Pattern"
            )
            predictions.append(pred_label)
            inference_times.append(inference_time)

        # Calculate metrics
        accuracy = accuracy_score(self.test_labels, predictions)
        precision = precision_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        recall = recall_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        f1 = f1_score(self.test_labels, predictions, average="macro", zero_division=0)

        avg_time = np.mean(inference_times) * 1000  # Convert to ms
        std_time = np.std(inference_times) * 1000

        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Avg Inference Time: {avg_time:.2f} ± {std_time:.2f} ms")

        return {
            "model": "Rule-Based",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_inference_time_ms": avg_time,
            "std_inference_time_ms": std_time,
            "predictions": predictions,
        }

    def benchmark_rule_based_with_sentiment(self) -> Dict:
        """Benchmark rule-based + sentiment detector."""
        print("\n" + "=" * 80)
        print("Benchmarking Rule-Based + Sentiment Detector")
        print("=" * 80)

        predictions = []
        inference_times = []

        for text in self.test_texts:
            start_time = time.time()
            result = self.rule_detector.analyze_element(text, use_sentiment=True)
            inference_time = time.time() - start_time

            pred_label = (
                result["primary_pattern"] if result["primary_pattern"] else "No Pattern"
            )
            predictions.append(pred_label)
            inference_times.append(inference_time)

        # Calculate metrics
        accuracy = accuracy_score(self.test_labels, predictions)
        precision = precision_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        recall = recall_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        f1 = f1_score(self.test_labels, predictions, average="macro", zero_division=0)

        avg_time = np.mean(inference_times) * 1000
        std_time = np.std(inference_times) * 1000

        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Avg Inference Time: {avg_time:.2f} ± {std_time:.2f} ms")

        return {
            "model": "Rule-Based + Sentiment",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_inference_time_ms": avg_time,
            "std_inference_time_ms": std_time,
            "predictions": predictions,
        }

    def benchmark_transformer(self) -> Dict:
        """Benchmark transformer detector."""
        print("\n" + "=" * 80)
        print("Benchmarking Transformer Detector")
        print("=" * 80)

        if not self.transformer_detector.model_available:
            print("Transformer model not available. Skipping...")
            return {
                "model": "Transformer",
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "avg_inference_time_ms": 0.0,
                "std_inference_time_ms": 0.0,
                "predictions": [],
                "available": False,
            }

        predictions = []
        inference_times = []

        for text in self.test_texts:
            start_time = time.time()
            result = self.transformer_detector.predict(text)
            inference_time = time.time() - start_time

            predictions.append(result["label"])
            inference_times.append(inference_time)

        # Calculate metrics
        accuracy = accuracy_score(self.test_labels, predictions)
        precision = precision_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        recall = recall_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        f1 = f1_score(self.test_labels, predictions, average="macro", zero_division=0)

        avg_time = np.mean(inference_times) * 1000
        std_time = np.std(inference_times) * 1000

        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Avg Inference Time: {avg_time:.2f} ± {std_time:.2f} ms")

        return {
            "model": "Transformer (DistilBERT)",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_inference_time_ms": avg_time,
            "std_inference_time_ms": std_time,
            "predictions": predictions,
            "available": True,
        }

    def benchmark_ensemble(self) -> Dict:
        """Benchmark ensemble detector."""
        print("\n" + "=" * 80)
        print("Benchmarking Ensemble Detector")
        print("=" * 80)

        predictions = []
        inference_times = []

        for text in self.test_texts:
            start_time = time.time()
            result = self.ensemble_detector.predict(text)
            inference_time = time.time() - start_time

            predictions.append(result["label"])
            inference_times.append(inference_time)

        # Calculate metrics
        accuracy = accuracy_score(self.test_labels, predictions)
        precision = precision_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        recall = recall_score(
            self.test_labels, predictions, average="macro", zero_division=0
        )
        f1 = f1_score(self.test_labels, predictions, average="macro", zero_division=0)

        avg_time = np.mean(inference_times) * 1000
        std_time = np.std(inference_times) * 1000

        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Avg Inference Time: {avg_time:.2f} ± {std_time:.2f} ms")

        return {
            "model": "Ensemble (Transformer + Rule-Based)",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_inference_time_ms": avg_time,
            "std_inference_time_ms": std_time,
            "predictions": predictions,
        }

    def run_all_benchmarks(self) -> List[Dict]:
        """Run all benchmarks."""
        results = []

        # Rule-based
        results.append(self.benchmark_rule_based())

        # Rule-based + Sentiment
        results.append(self.benchmark_rule_based_with_sentiment())

        # Transformer
        transformer_result = self.benchmark_transformer()
        if transformer_result.get("available", False):
            results.append(transformer_result)

        # Ensemble
        results.append(self.benchmark_ensemble())

        return results

    def generate_comparison_report(
        self, results: List[Dict], output_path="MODEL_COMPARISON.md"
    ):
        """Generate markdown comparison report."""
        report = []

        report.append("# Model Comparison Report")
        report.append("## PatternShield Dark Pattern Detection Models\n")
        report.append("---\n")

        # Summary table
        report.append("## Performance Comparison\n")
        report.append(
            "| Model | Accuracy | Precision | Recall | F1 Score | Avg Time (ms) |"
        )
        report.append(
            "|-------|----------|-----------|--------|----------|---------------|"
        )

        for result in results:
            report.append(
                f"| {result['model']} | "
                f"{result['accuracy']:.4f} | "
                f"{result['precision']:.4f} | "
                f"{result['recall']:.4f} | "
                f"{result['f1_score']:.4f} | "
                f"{result['avg_inference_time_ms']:.2f} ± {result['std_inference_time_ms']:.2f} |"
            )

        report.append("\n---\n")

        # Best model
        best_f1 = max(results, key=lambda x: x["f1_score"])
        fastest = min(results, key=lambda x: x["avg_inference_time_ms"])

        report.append("## Key Findings\n")
        report.append(
            f"**Best F1 Score**: {best_f1['model']} ({best_f1['f1_score']:.4f})\n"
        )
        report.append(
            f"**Fastest Inference**: {fastest['model']} ({fastest['avg_inference_time_ms']:.2f} ms)\n"
        )

        # Speed vs Accuracy tradeoff
        report.append("\n## Speed vs Accuracy Tradeoff\n")
        for result in sorted(results, key=lambda x: x["avg_inference_time_ms"]):
            efficiency = result["f1_score"] / (result["avg_inference_time_ms"] / 1000)
            report.append(
                f"- **{result['model']}**: {result['f1_score']:.4f} F1 @ {result['avg_inference_time_ms']:.1f}ms "
                f"(Efficiency: {efficiency:.2f})\n"
            )

        # Recommendations
        report.append("\n## Recommendations\n")
        report.append("### For Production Deployment:\n")

        if best_f1["model"] == fastest["model"]:
            report.append(
                f"- **{best_f1['model']}** offers the best balance of accuracy and speed\n"
            )
        else:
            report.append(
                f"- **For accuracy-critical applications**: Use {best_f1['model']}\n"
            )
            report.append(
                f"- **For latency-sensitive applications**: Use {fastest['model']}\n"
            )
            report.append(
                f"- **For balanced performance**: Consider ensemble approach\n"
            )

        report.append("\n### Model Selection Guide:\n")
        report.append(
            "- **Rule-Based**: Fastest, interpretable, no training required\n"
        )
        report.append(
            "- **Rule-Based + Sentiment**: Slight improvement with minimal overhead\n"
        )
        report.append(
            "- **Transformer**: Highest accuracy, requires GPU for fast inference\n"
        )
        report.append(
            "- **Ensemble**: Best overall performance, combines strengths of both\n"
        )

        report.append("\n---\n")
        report.append("## Methodology\n")
        report.append(f"- **Test Set Size**: {len(self.test_texts)} examples\n")
        report.append(
            "- **Metrics**: Accuracy, Precision, Recall, F1 Score (Macro Average)\n"
        )
        report.append("- **Inference Time**: Average over all test examples\n")
        report.append("- **Hardware**: CPU-based inference\n")

        report.append("\n---\n")
        report.append("*Report generated by model_comparison.py*\n")

        # Write report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"\n{'='*80}")
        print(f"Comparison report saved to {output_path}")
        print("=" * 80)


def main():
    print("=" * 80)
    print("MODEL COMPARISON BENCHMARK")
    print("=" * 80)

    # Run benchmarks
    benchmark = ModelBenchmark()
    results = benchmark.run_all_benchmarks()

    # Generate report
    benchmark.generate_comparison_report(results)

    # Save results to JSON
    results_path = "model_comparison_results.json"
    with open(results_path, "w") as f:
        # Remove predictions from JSON to keep file size small
        results_clean = [
            {k: v for k, v in r.items() if k != "predictions"} for r in results
        ]
        json.dump(results_clean, f, indent=2)

    print(f"\nResults also saved to {results_path}")
    print("\n✓ Benchmark complete!")


if __name__ == "__main__":
    main()
