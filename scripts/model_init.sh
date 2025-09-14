#!/bin/sh
# POSIX sh
set -eu

# Expected from .env (via compose):
#   MODEL_FILE=/models/softball.Q4_K_M.gguf
#   LLM_MODEL_NAME=softball-q4           (or softball-q4:latest — both ok)

echo "model-init: using file ${MODEL_FILE:-/models/softball.Q4_K_M.gguf}"
MODEL_FILE="${MODEL_FILE:-/models/softball.Q4_K_M.gguf}"
LLM_MODEL_NAME="${LLM_MODEL_NAME:-softball-q4}"

if [ ! -f "$MODEL_FILE" ]; then
  echo "ERROR: model file not found at $MODEL_FILE"
  exit 2
fi

# Create an Ollama ModelFile pointing at your GGUF
printf "FROM %s\n" "$MODEL_FILE" > /models/ModelFile

# Create the model if it doesn't exist (use the name exactly as given)
if ! ollama show "$LLM_MODEL_NAME" >/dev/null 2>&1; then
  echo "Creating Ollama model: $LLM_MODEL_NAME"
  ollama create "$LLM_MODEL_NAME" -f /models/ModelFile
else
  echo "Ollama model $LLM_MODEL_NAME already present"
fi

echo "model-init: done."
