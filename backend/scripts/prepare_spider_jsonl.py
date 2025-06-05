import json
from pathlib import Path
import argparse


def load_schema(tables_path: Path) -> dict:
    """Return mapping of db_id -> schema string."""
    with open(tables_path, 'r') as f:
        tables = json.load(f)

    schemas = {}
    for db in tables:
        table_names = db["table_names_original"]
        columns = db["column_names_original"]
        parts = []
        for idx, table_name in enumerate(table_names):
            cols = [col for tbl_idx, col in columns if tbl_idx == idx and col != "*"]
            parts.append(f"{table_name}({','.join(cols)})")
        schemas[db["db_id"]] = " ".join(parts)
    return schemas


def convert(json_file: Path, schema_map: dict):
    with open(json_file, 'r') as f:
        examples = json.load(f)

    for ex in examples:
        db = ex["db_id"]
        schema = schema_map[db]
        prompt = f"Schema: {schema}\nQuestion: {ex['question']}\nSQL:"
        yield {"prompt": prompt, "response": ex["query"]}


def dump_jsonl(files, out_path: Path, schema_map: dict):
    with open(out_path, 'w') as f:
        for jf in files:
            for item in convert(jf, schema_map):
                json.dump(item, f)
                f.write('\n')


def main(args):
    spider_dir = Path(args.spider_dir)
    schema_map = load_schema(spider_dir / 'tables.json')

    train_files = [spider_dir / 'train_spider.json', spider_dir / 'train_others.json']
    val_files = [spider_dir / 'dev.json']

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dump_jsonl(train_files, out_dir / args.train_file, schema_map)
    dump_jsonl(val_files, out_dir / args.val_file, schema_map)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare Spider dataset in JSONL format for training.')
    parser.add_argument('--spider-dir', default='spider_data', help='Path to raw Spider dataset directory')
    parser.add_argument('--output-dir', default='.', help='Directory to save JSONL files')
    parser.add_argument('--train-file', default='spider_train.jsonl', help='Name of output training JSONL file')
    parser.add_argument('--val-file', default='spider_val.jsonl', help='Name of output validation JSONL file')

    main(parser.parse_args())
