import subprocess
import os
import time

AVAILABLE = ["qwen2.5:3b", "llama3.1:8b", "gpt-oss:20b"]
SELECTED_MODEL = os.environ.get("SELECTED_MODEL") or "qwen2.5:3b"

def is_ollama_healthy():
    try:
        out = subprocess.check_output([
            "docker", "inspect", "--format={{.State.Health.Status}}", "ollama"
        ], text=True).strip()
        return out == "healthy"
    except Exception:
        return False

def wait_ollama():
    for _ in range(20):
        if is_ollama_healthy():
            return True
        print("Waiting for ollama to be healthy...")
        time.sleep(2)
    return False

def list_models():
    try:
        out = subprocess.check_output([
            "docker", "exec", "-i", "ollama", "ollama", "list"
        ], text=True)
        return [line.split()[0] for line in out.splitlines()[1:] if line.strip()]
    except Exception:
        return []

def pull_model(model):
    print(f"Pulling model: {model}")
    subprocess.run([
        "docker", "exec", "-i", "ollama", "ollama", "pull", model
    ], check=True)

def ensure_model():
    # Ensure ollama is running
    try:
        running = subprocess.check_output([
            "docker", "ps", "--format", "{{.Names}}"
        ], text=True)
        if "ollama" not in running:
            print("Starting ollama service...")
            subprocess.run(["docker", "compose", "up", "-d", "ollama"], check=True)
    except Exception as e:
        print("Error checking/starting ollama:", e)
        return False

    if not wait_ollama():
        print("Ollama did not become healthy in time.")
        return False

    current = list_models()
    for m in AVAILABLE:
        if m in current:
            print(f"Model present: {m}")
            return True

    # None present, pull selected
    model = SELECTED_MODEL
    pull_model(model)
    print("Current models:", list_models())
    return True

if __name__ == "__main__":
    ensure_model()