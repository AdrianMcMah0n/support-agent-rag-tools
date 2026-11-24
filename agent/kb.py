"""Knowledge base: split the markdown docs into sections, embed them once (cached), search by cosine similarity."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / 'kb'
INDEX = ROOT / 'data' / 'kb_index.json'
EMBED_MODEL = 'text-embedding-3-small'


def chunks(kb_dir: Path = KB_DIR) -> list[dict]:
    """One chunk per '## ' section. Chunk id = '<file>#<n>', e.g. 'returns#1', used for citations."""
    out = []
    for doc in sorted(kb_dir.glob('*.md')):
        title = doc.read_text(encoding='utf-8').splitlines()[0].lstrip('# ').strip()
        for n, sec in enumerate(re.split(r'\n(?=## )', doc.read_text(encoding='utf-8'))[1:], 1):
            heading, _, body = sec.partition('\n')
            out.append({'id': f'{doc.stem}#{n}', 'title': f"{title} > {heading.lstrip('# ').strip()}", 'text': body.strip()})
    return out


class KnowledgeBase:
    def __init__(self, client: OpenAI):
        self.client = client
        self.chunks = chunks()
        key = hashlib.sha256(json.dumps(self.chunks).encode()).hexdigest()
        cached = json.loads(INDEX.read_text()) if INDEX.exists() else {}
        if cached.get('key') != key:  # re-embed only when the documents change
            vecs = client.embeddings.create(model=EMBED_MODEL, input=[f"{c['title']}\n{c['text']}" for c in self.chunks])
            cached = {'key': key, 'vectors': [d.embedding for d in vecs.data]}
            INDEX.write_text(json.dumps(cached))
        m = np.array(cached['vectors'])
        self.matrix = m / np.linalg.norm(m, axis=1, keepdims=True)

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = np.array(self.client.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding)
        scores = self.matrix @ (q / np.linalg.norm(q))
        best = np.argsort(-scores)[:k]
        return [{**self.chunks[i], 'score': round(float(scores[i]), 3)} for i in best]
