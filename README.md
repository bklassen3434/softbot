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

## Running Tests

PyTest modules under `tests/` validate the backend components. The training
script is exercised on a tiny dummy dataset to ensure it runs end-to-end.

Run all tests with:

```bash
pytest -q
```

The training test requires access to the base Qwen model on HuggingFace and may
take several minutes depending on hardware.
