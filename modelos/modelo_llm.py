# modelo_llm.py
import json
import httpx
from typing import Generator

OLLAMA_URL = "http://172.16.188.33:3003/api/generate"
MODEL_NAME = "mistral:latest"

def stream_llm_tokens(prompt: str) -> Generator[str, None, None]:
    """
    Conecta en streaming con Ollama y va yield-eando cada token a medida que llega.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": True}
    with httpx.Client(timeout=None) as client:
        with client.stream("POST", OLLAMA_URL, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines():
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    pkt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = pkt.get("token") or pkt.get("response", "")
                if token:
                    yield token
