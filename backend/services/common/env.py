from dotenv import load_dotenv
import os

def load_env():
    # Load from project root .env if present
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    env_path = os.path.join(root, '.env')
    load_dotenv(env_path)
    return env_path

def get(key: str, default: str|None=None) -> str|None:
    return os.environ.get(key, default)
