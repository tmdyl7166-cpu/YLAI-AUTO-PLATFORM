#!/usr/bin/env bash
set -euo pipefail
# Usage: ./watch/select_model.sh <model>
# Example: ./watch/select_model.sh qwen2.5:3b

MODEL=${1:-}
if [[ -z "$MODEL" ]]; then
  echo "Usage: $0 <model>"
  echo "Models: qwen2.5:3b | llama3.1:8b | gpt-oss:20b"
  exit 2
fi

# Ensure ollama service is up
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

# Check if model exists
if docker exec -i ollama ollama list | awk '{print $1}' | grep -q "^${MODEL}$"; then
  echo "Model already present: ${MODEL}"
else
  echo "Pulling model: ${MODEL}"
  docker exec -it ollama ollama pull "$MODEL"
fi

echo "Current models:" 
docker exec -i ollama ollama list
