#!/usr/bin/env bash
set -euo pipefail
# Ensure a model exists in Ollama. If none, ask user to choose.
# Usage: ./watch/ensure_model.sh [model]
# Models: qwen2.5:3b | llama3.1:8b | gpt-oss:20b

MODEL=${1:-${SELECTED_MODEL:-}}
AVAILABLE=("qwen2.5:3b" "llama3.1:8b" "gpt-oss:20b")

# Ensure ollama service is running
if ! docker ps --format '{{.Names}}' | grep -q '^ollama$'; then
  echo "Starting ollama service..."
  docker compose up -d ollama
fi

# Wait for health
for i in {1..20}; do
  s=$(docker inspect --format='{{.State.Health.Status}}' ollama 2>/dev/null || echo starting)
  echo "ollama health: $s"
  [[ "$s" == "healthy" ]] && break
  sleep 2
done

# If any of the AVAILABLE models exists, just run.
HAS_ANY=0
CURRENT=$(docker exec -i ollama ollama list | awk 'NR>1{print $1}') || true
for m in ${AVAILABLE[@]}; do
  if echo "$CURRENT" | grep -qx "$m"; then HAS_ANY=1; MODEL="$m"; break; fi
done

if [[ $HAS_ANY -eq 1 ]]; then
  echo "Model present: $MODEL — no pull needed"
else
  # No available model, ask user to choose
  echo "No required models found. Please choose one to pull:"
  PS3="Select model (1-3): "
  select choice in "qwen2.5:3b" "llama3.1:8b" "gpt-oss:20b"; do
    if [[ -n "${choice:-}" ]]; then MODEL="$choice"; break; fi
  done
  echo "Pulling $MODEL ..."
  docker exec -it ollama ollama pull "$MODEL"
fi

echo "Current models:"
docker exec -i ollama ollama list
