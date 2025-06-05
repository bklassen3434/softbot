import argparse
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

def load_data(train_file: str, val_file: str):
    dataset = load_dataset('json', data_files={'train': train_file, 'validation': val_file})

    def tokenize_fn(example):
        tokenized = tokenizer(example['prompt'], truncation=True)
        labels = tokenizer(example['response'], truncation=True)
        tokenized['labels'] = labels['input_ids']
        return tokenized

    return dataset.map(tokenize_fn, batched=True, remove_columns=dataset['train'].column_names)

def main(args):
    global tokenizer
    model_name = args.model_name
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    tokenized_ds = load_data(args.train_file, args.val_file)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["W_pack", "O_pack"],
    )
    model = get_peft_model(model, lora_config)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        num_train_epochs=3,
        save_total_limit=2,
        logging_steps=50,
        evaluation_strategy="epoch",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds['train'],
        eval_dataset=tokenized_ds['validation'],
    )

    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Qwen on the Spider dataset")
    parser.add_argument("--train-file", required=True, help="Path to training JSONL")
    parser.add_argument("--val-file", required=True, help="Path to validation JSONL")
    parser.add_argument("--output-dir", default="qwen_spider_finetuned", help="Where to save the model")
    parser.add_argument("--model-name", default="Qwen/Qwen-7B", help="Base Qwen model")
    args = parser.parse_args()
    main(args)
