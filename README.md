# SoftBot

This repository contains a simple chat application with a FastAPI backend and a React frontend.

## Fine-tuning Qwen on Spider

A script is provided to fine-tune a Qwen model on the Spider text-to-SQL dataset.
The raw Spider files are included under `spider_data/`. Convert them into the
required JSONL format using `prepare_spider_jsonl.py`:

```bash
python backend/scripts/prepare_spider_jsonl.py --spider-dir spider_data --output-dir .
```

This will generate `spider_train.jsonl` and `spider_val.jsonl` containing
`prompt` and `response` fields. Then run the training script:

```bash
python backend/scripts/train_qwen_spider.py \
    --train-file data/spider_train.jsonl \
    --val-file data/spider_val.jsonl \
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