#!/bin/bash
# Train DistilBERT for Dark Pattern Classification

set -e

echo "=============================================="
echo "PatternShield Transformer Training"
echo "=============================================="
echo ""

# Configuration
MODEL="distilbert-base-uncased"
EPOCHS=10
BATCH_SIZE=16
LEARNING_RATE=2e-5
PATIENCE=3
OUTPUT_DIR="models/distilbert_darkpattern"
DATA_PATH="data/training_dataset.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --epochs)
            EPOCHS="$2"
            shift 2
            ;;
        --batch_size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --lr)
            LEARNING_RATE="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Training Configuration:"
echo "  Model: $MODEL"
echo "  Epochs: $EPOCHS"
echo "  Batch Size: $BATCH_SIZE"
echo "  Learning Rate: $LEARNING_RATE"
echo "  Patience: $PATIENCE"
echo "  Output Dir: $OUTPUT_DIR"
echo "  Data Path: $DATA_PATH"
echo ""

# Check if data exists
if [ ! -f "$DATA_PATH" ]; then
    echo "Error: Training data not found at $DATA_PATH"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p "training_logs"

echo "Starting training..."
echo ""

# Run training
python train_transformer.py \
    --model "$MODEL" \
    --epochs "$EPOCHS" \
    --batch_size "$BATCH_SIZE" \
    --lr "$LEARNING_RATE" \
    --patience "$PATIENCE" \
    --output_dir "$OUTPUT_DIR" \
    --data_path "$DATA_PATH"

echo ""
echo "=============================================="
echo "Training Complete!"
echo "=============================================="
echo ""
echo "Model saved to: $OUTPUT_DIR/best_model"
echo "Training logs: training_logs/"
echo ""
echo "View training progress:"
echo "  tensorboard --logdir=training_logs"
echo ""
echo "Test the model:"
echo "  python transformer_detector.py"
echo ""
