import json
import subprocess
from pathlib import Path
import sys
import tempfile
import pytest

# Skip if required ML libraries are missing
pytest.importorskip("datasets")
pytest.importorskip("transformers")
pytest.importorskip("peft")


def _create_dummy_jsonl(path: Path) -> None:
    sample = {
        "prompt": "Schema: students(id,name)\nQuestion: how many students exist?\nSQL:",
        "response": "SELECT COUNT(*) FROM students;",
    }
    with open(path, "w") as f:
        json.dump(sample, f)
        f.write("\n")


def test_training_script(tmp_path: Path):
    train_file = tmp_path / "train.jsonl"
    val_file = tmp_path / "val.jsonl"
    _create_dummy_jsonl(train_file)
    _create_dummy_jsonl(val_file)
    model_dir = tmp_path / "model"

    script = Path(__file__).resolve().parents[1] / "backend/scripts/train_qwen_spider.py"
    cmd = [
        sys.executable,
        str(script),
        "--train-file", str(train_file),
        "--val-file", str(val_file),
        "--output-dir", str(model_dir),
        "--model-name", "Qwen/Qwen-7B",
    ]

    subprocess.run(cmd, check=True)
    assert any(model_dir.iterdir())
