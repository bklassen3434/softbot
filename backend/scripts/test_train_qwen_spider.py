import json
import subprocess
import tempfile
from pathlib import Path


def _create_dummy_jsonl(path: Path):
    """Write a single dummy prompt/response pair to `path`."""
    sample = {
        "prompt": "Schema: students(id,name)\nQuestion: how many students exist?\nSQL:",
        "response": "SELECT COUNT(*) FROM students;"
    }
    with open(path, "w") as f:
        json.dump(sample, f)
        f.write("\n")


def main():
    """Run the training script on a tiny dataset and verify output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        train_file = tmp_path / "train.jsonl"
        val_file = tmp_path / "val.jsonl"
        _create_dummy_jsonl(train_file)
        _create_dummy_jsonl(val_file)

        model_dir = tmp_path / "model"

        cmd = [
            "python",
            str(Path(__file__).with_name("train_qwen_spider.py")),
            "--train-file",
            str(train_file),
            "--val-file",
            str(val_file),
            "--output-dir",
            str(model_dir),
            "--model-name",
            "Qwen/Qwen-7B"
        ]
        subprocess.run(cmd, check=True)

        if not any(model_dir.iterdir()):
            raise RuntimeError("Training did not produce any model files")
        print("Test completed successfully. Model files found in", model_dir)


if __name__ == "__main__":
    main()
