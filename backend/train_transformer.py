"""
Fine-tune DistilBERT for Dark Pattern Classification
6-way classification: Urgency/Scarcity, Confirmshaming, Obstruction,
Visual Interference, Sneaking, No Pattern
"""

import json
import os
import random
import argparse
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.utils.tensorboard import SummaryWriter
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    AdamW,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import accuracy_score, f1_score, classification_report
from tqdm import tqdm

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)


class DarkPatternDataset(Dataset):
    """Dataset for dark pattern text classification."""

    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


class DarkPatternTrainer:
    """Trainer for DistilBERT dark pattern classifier."""

    def __init__(
        self,
        model_name="distilbert-base-uncased",
        num_classes=6,
        output_dir="models/distilbert_darkpattern",
        log_dir="training_logs",
    ):
        self.model_name = model_name
        self.num_classes = num_classes
        self.output_dir = output_dir
        self.log_dir = log_dir

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Label mapping
        self.label2id = {
            "Urgency/Scarcity": 0,
            "Confirmshaming": 1,
            "Obstruction": 2,
            "Visual Interference": 3,
            "Sneaking": 4,
            "No Pattern": 5,
        }
        self.id2label = {v: k for k, v in self.label2id.items()}

        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # TensorBoard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.writer = SummaryWriter(f"{self.log_dir}/run_{timestamp}")

        # Initialize model and tokenizer
        print(f"Loading {model_name}...")
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_name, num_labels=num_classes, dropout=0.3
        )
        self.model.to(self.device)

        print(
            f"Model loaded with {sum(p.numel() for p in self.model.parameters())} parameters"
        )

    def load_data(self, data_path="data/training_dataset.json"):
        """Load and prepare datasets."""
        print(f"\nLoading data from {data_path}...")

        with open(data_path, "r") as f:
            data = json.load(f)

        # Process train data
        train_texts = [ex["text"] for ex in data["train"]]
        train_labels = [self.label2id[ex["label"]] for ex in data["train"]]

        # Process validation data
        val_texts = [ex["text"] for ex in data["validation"]]
        val_labels = [self.label2id[ex["label"]] for ex in data["validation"]]

        # Process test data
        test_texts = [ex["text"] for ex in data["test"]]
        test_labels = [self.label2id[ex["label"]] for ex in data["test"]]

        print(
            f"Train: {len(train_texts)} | Val: {len(val_texts)} | Test: {len(test_texts)}"
        )

        # Create datasets
        self.train_dataset = DarkPatternDataset(
            train_texts, train_labels, self.tokenizer
        )
        self.val_dataset = DarkPatternDataset(val_texts, val_labels, self.tokenizer)
        self.test_dataset = DarkPatternDataset(test_texts, test_labels, self.tokenizer)

        return train_texts, train_labels, val_texts, val_labels, test_texts, test_labels

    def create_dataloaders(self, batch_size=16):
        """Create data loaders."""
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True,
        )

        self.val_loader = DataLoader(
            self.val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True,
        )

        self.test_loader = DataLoader(
            self.test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True,
        )

        print(f"Dataloaders created: {len(self.train_loader)} train batches")

    def setup_optimizer(self, lr=2e-5, epochs=10):
        """Setup optimizer and scheduler."""
        # Optimizer
        self.optimizer = AdamW(self.model.parameters(), lr=lr)

        # Learning rate scheduler with warmup
        num_training_steps = len(self.train_loader) * epochs
        num_warmup_steps = num_training_steps // 10

        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps,
        )

        print(f"Optimizer: AdamW (lr={lr})")
        print(f"Warmup steps: {num_warmup_steps} / {num_training_steps}")

    def train_epoch(self, epoch):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        predictions = []
        true_labels = []

        progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch}")

        for batch_idx, batch in enumerate(progress_bar):
            # Move to device
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)

            # Forward pass
            outputs = self.model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )

            loss = outputs.loss
            logits = outputs.logits

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            self.scheduler.step()

            # Track metrics
            total_loss += loss.item()
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            predictions.extend(preds)
            true_labels.extend(labels.cpu().numpy())

            # Update progress bar
            progress_bar.set_postfix({"loss": loss.item()})

            # Log to TensorBoard
            global_step = epoch * len(self.train_loader) + batch_idx
            self.writer.add_scalar("Train/Loss", loss.item(), global_step)
            self.writer.add_scalar(
                "Train/LR", self.scheduler.get_last_lr()[0], global_step
            )

        # Epoch metrics
        avg_loss = total_loss / len(self.train_loader)
        accuracy = accuracy_score(true_labels, predictions)
        f1 = f1_score(true_labels, predictions, average="macro")

        return avg_loss, accuracy, f1

    def validate(self, epoch):
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        predictions = []
        true_labels = []

        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )

                loss = outputs.loss
                logits = outputs.logits

                total_loss += loss.item()
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                predictions.extend(preds)
                true_labels.extend(labels.cpu().numpy())

        # Metrics
        avg_loss = total_loss / len(self.val_loader)
        accuracy = accuracy_score(true_labels, predictions)
        f1 = f1_score(true_labels, predictions, average="macro")

        # Log to TensorBoard
        self.writer.add_scalar("Val/Loss", avg_loss, epoch)
        self.writer.add_scalar("Val/Accuracy", accuracy, epoch)
        self.writer.add_scalar("Val/F1", f1, epoch)

        return avg_loss, accuracy, f1, predictions, true_labels

    def train(self, epochs=10, batch_size=16, lr=2e-5, patience=3):
        """Full training loop with early stopping."""
        print("\n" + "=" * 80)
        print("STARTING TRAINING")
        print("=" * 80)

        # Setup
        self.create_dataloaders(batch_size)
        self.setup_optimizer(lr, epochs)

        # Early stopping
        best_f1 = 0
        patience_counter = 0

        # Training loop
        for epoch in range(1, epochs + 1):
            print(f"\n{'='*80}")
            print(f"Epoch {epoch}/{epochs}")
            print(f"{'='*80}")

            # Train
            train_loss, train_acc, train_f1 = self.train_epoch(epoch)
            print(
                f"Train Loss: {train_loss:.4f} | Acc: {train_acc:.4f} | F1: {train_f1:.4f}"
            )

            # Validate
            val_loss, val_acc, val_f1, val_preds, val_labels = self.validate(epoch)
            print(f"Val Loss: {val_loss:.4f} | Acc: {val_acc:.4f} | F1: {val_f1:.4f}")

            # Log epoch metrics
            self.writer.add_scalars(
                "Loss", {"train": train_loss, "val": val_loss}, epoch
            )
            self.writer.add_scalars(
                "Accuracy", {"train": train_acc, "val": val_acc}, epoch
            )
            self.writer.add_scalars("F1", {"train": train_f1, "val": val_f1}, epoch)

            # Save checkpoint
            checkpoint_path = os.path.join(
                self.output_dir, f"checkpoint_epoch_{epoch}.pt"
            )
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "val_f1": val_f1,
                },
                checkpoint_path,
            )
            print(f"Checkpoint saved: {checkpoint_path}")

            # Early stopping check
            if val_f1 > best_f1:
                best_f1 = val_f1
                patience_counter = 0

                # Save best model
                best_model_path = os.path.join(self.output_dir, "best_model")
                self.model.save_pretrained(best_model_path)
                self.tokenizer.save_pretrained(best_model_path)
                print(
                    f"✓ New best model! F1: {best_f1:.4f} (saved to {best_model_path})"
                )
            else:
                patience_counter += 1
                print(f"No improvement. Patience: {patience_counter}/{patience}")

                if patience_counter >= patience:
                    print(f"\nEarly stopping triggered after {epoch} epochs")
                    break

        print(f"\n{'='*80}")
        print("TRAINING COMPLETE")
        print(f"Best Validation F1: {best_f1:.4f}")
        print("=" * 80)

        self.writer.close()
        return best_f1

    def evaluate_test(self):
        """Evaluate on test set."""
        print("\n" + "=" * 80)
        print("EVALUATING ON TEST SET")
        print("=" * 80)

        # Load best model
        best_model_path = os.path.join(self.output_dir, "best_model")
        self.model = DistilBertForSequenceClassification.from_pretrained(
            best_model_path
        )
        self.model.to(self.device)
        self.model.eval()

        predictions = []
        true_labels = []

        with torch.no_grad():
            for batch in tqdm(self.test_loader, desc="Testing"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits

                preds = torch.argmax(logits, dim=1).cpu().numpy()
                predictions.extend(preds)
                true_labels.extend(labels.cpu().numpy())

        # Metrics
        accuracy = accuracy_score(true_labels, predictions)
        f1_macro = f1_score(true_labels, predictions, average="macro")
        f1_weighted = f1_score(true_labels, predictions, average="weighted")

        print(f"\nTest Results:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Macro F1: {f1_macro:.4f}")
        print(f"Weighted F1: {f1_weighted:.4f}")

        # Classification report
        print("\nPer-Class Metrics:")
        print(
            classification_report(
                true_labels,
                predictions,
                target_names=list(self.label2id.keys()),
                digits=4,
            )
        )

        # Save test results
        results = {
            "accuracy": float(accuracy),
            "f1_macro": float(f1_macro),
            "f1_weighted": float(f1_weighted),
            "classification_report": classification_report(
                true_labels,
                predictions,
                target_names=list(self.label2id.keys()),
                output_dict=True,
            ),
        }

        results_path = os.path.join(self.output_dir, "test_results.json")
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nTest results saved to {results_path}")

        return accuracy, f1_macro, predictions, true_labels


def main():
    parser = argparse.ArgumentParser(
        description="Train DistilBERT for dark pattern classification"
    )
    parser.add_argument(
        "--model", type=str, default="distilbert-base-uncased", help="Base model"
    )
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument(
        "--patience", type=int, default=3, help="Early stopping patience"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/distilbert_darkpattern",
        help="Output directory",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="data/training_dataset.json",
        help="Training data path",
    )

    args = parser.parse_args()

    # Initialize trainer
    trainer = DarkPatternTrainer(model_name=args.model, output_dir=args.output_dir)

    # Load data
    trainer.load_data(args.data_path)

    # Train
    best_f1 = trainer.train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
    )

    # Evaluate on test set
    trainer.evaluate_test()

    print("\n✓ Training pipeline complete!")


if __name__ == "__main__":
    main()
