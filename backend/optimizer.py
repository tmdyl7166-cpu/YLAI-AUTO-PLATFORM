import json
import urllib.request
from typing import List, Dict, Optional

from config import OLLAMA_URL, OLLAMA_MODEL


def _ollama_generate(prompt: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 512) -> str:
	url = OLLAMA_URL
	m = model or OLLAMA_MODEL
	payload = {
		"model": m,
		"prompt": prompt,
		"temperature": temperature,
		"max_tokens": max_tokens,
		"stream": False,
	}
	body = json.dumps(payload).encode("utf-8")
	headers = {"Content-Type": "application/json"}
	req = urllib.request.Request(url, data=body, headers=headers)
	with urllib.request.urlopen(req, timeout=60) as resp:
		data = json.loads(resp.read().decode("utf-8"))
		# Ollama generate returns {response: "..."}
		return data.get("response", "")


def auto_optimize(text: str, suggestions: List[Dict]) -> str:
	# If no suggestions, short-circuit
	if not suggestions:
		return text

	# Fallback naive replacement, in case model fails
	def _fallback(t: str) -> str:
		out = t
		for s in suggestions:
			kw = s.get("keyword")
			if kw and kw in out:
				out = out.replace(kw, f"# FIXED: {kw}")
		return out

	try:
		# Construct a concise instruction to rewrite code with rules
		# Keep deterministic style, avoid hallucinations
		prompt = (
			"You are a coding optimizer. "
			"Improve the following Python code strictly according to "
			"the issues hinted by keywords, while preserving behavior. "
			"Apply minimal, safe fixes, add types where trivial, and keep "
			"formatting stable.\n\n"
			f"Keywords: {[s.get('keyword') for s in suggestions if s.get('keyword')]}\n\n"
			f"Code:\n```python\n{text}\n```\n\n"
			"Return only the rewritten code."
		)
		response = _ollama_generate(prompt)
		# Strip potential markdown fences
		cleaned = response.strip()
		if cleaned.startswith("```"):
			cleaned = cleaned.strip("`\n").split("python\n", 1)[-1]
		return cleaned if cleaned else _fallback(text)
	except Exception:
		return _fallback(text)
