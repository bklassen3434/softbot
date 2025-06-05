# SoftBot

This repository contains a simple chat application with a FastAPI backend and a React frontend.

## Fine-tuning Qwen on Spider

A script is provided to fine-tune a Qwen model on the Spider text-to-SQL dataset. Prepare your dataset as JSONL files containing `prompt` and `response` fields and run:

```bash
python backend/scripts/train_qwen_spider.py \
    --train-file spider_train.jsonl \
    --val-file spider_val.jsonl \
    --output-dir qwen_spider_finetuned
```

After training, set the `LOCAL_MODEL_PATH` environment variable to the directory that contains the saved model. The backend will automatically load this local model via HuggingFace and use it for query generation instead of OpenAI.

## Testing the Training Script

The `backend/scripts/test_train_qwen_spider.py` script runs a minimal training cycle using a dummy dataset. It verifies that the training script completes and produces model files.

```bash
python backend/scripts/test_train_qwen_spider.py
```

This test requires access to the base Qwen model on HuggingFace and may take several minutes depending on hardware.
