from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from ..config import settings
import numpy as np
from tqdm import tqdm
import uuid

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "jailbreak_prompts"

# Lazy singleton pattern
_model = None
_client = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client

def _ensure_collection():
    client = _get_client()
    if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=rest.VectorParams(size=384, distance=rest.Distance.COSINE),
        )

#def bootstrap(jailbreak_prompts: list[str]):
#    """Populate the vector DB once."""
#    _ensure_collection()
#    model = _get_model()
#    client = _get_client()
#    embeddings = model.encode(jailbreak_prompts).tolist()
#    points = [rest.PointStruct(id=i, vector=emb, payload={}) for i, emb in enumerate(embeddings)]
#    client.upsert(collection_name=COLLECTION_NAME, points=points)

def bootstrap(jailbreak_prompts: list[str]):
    """Populate the vector DB in batches."""
    _ensure_collection()
    model = _get_model()
    client = _get_client()

    BATCH_SIZE = 128
    for i in tqdm(range(0, len(jailbreak_prompts), BATCH_SIZE), desc="Upserting to Qdrant"):
        batch = jailbreak_prompts[i:i + BATCH_SIZE]
        embeddings = model.encode(batch).tolist()
        points = [
            rest.PointStruct(id=str(uuid.uuid4()), vector=emb, payload={"prompt": text})
            for emb, text in zip(embeddings, batch)
        ]
        client.upsert(collection_name=COLLECTION_NAME, points=points)

def is_prompt_injection_semantic(prompt: str) -> bool:
    """Return True if cosine similarity >= threshold."""
    _ensure_collection()
    model = _get_model()
    client = _get_client()
    vector = model.encode(prompt).tolist()
    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=1,
        score_threshold=settings.semantic_threshold,
    )
    return len(hits) > 0

def cosine_similarity_score(prompt: str) -> float:
    _ensure_collection()
    vector = _get_model().encode(prompt).tolist()
    hits = _get_client().search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=1
    )
    return hits[0].score if hits else 0.0
