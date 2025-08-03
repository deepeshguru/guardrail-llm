from __future__ import annotations

import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from guardrail_proxy.config import settings
from guardrail_proxy.utils.role_context import role_cfg

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_COLLECTION = "jailbreak_prompts"


class _Lazy:
    """Simple lazy singletons for model and client."""
    model: SentenceTransformer | None = None
    client: QdrantClient | None = None


def _get_model() -> SentenceTransformer:
    if _Lazy.model is None:
        _Lazy.model = SentenceTransformer(_MODEL_NAME)
    return _Lazy.model


def _get_client() -> QdrantClient:
    if _Lazy.client is None:
        _Lazy.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _Lazy.client


def _ensure_collection() -> None:
    cl = _get_client()
    if _COLLECTION not in [c.name for c in cl.get_collections().collections]:
        cl.recreate_collection(
            collection_name=_COLLECTION,
            vectors_config=rest.VectorParams(size=384, distance=rest.Distance.COSINE),
        )


class SemanticFilter:
    """Layer-B semantic similarity guardrail."""

    def __init__(self) -> None:
        _ensure_collection()
        self.model = _get_model()
        self.client = _get_client()

    # --------------- public API --------------- #
    def is_blocked(self, prompt: str, role: str = "guest") -> bool:
        vec = self.model.encode(prompt).tolist()
        thresh = settings.base_semantic_threshold + role_cfg(role).get(
            "semantic_threshold_delta", 0.0
        )
        hits = self.client.search(
            collection_name=_COLLECTION,
            query_vector=vec,
            limit=1,
            score_threshold=thresh,
        )
        return bool(hits)

    # --------------- helper ------------------- #
    @staticmethod
    def bootstrap(jailbreak_prompts: List[str]) -> None:
        _ensure_collection()
        model = _get_model()
        client = _get_client()
        BATCH = 128
        for i in tqdm(
            range(0, len(jailbreak_prompts), BATCH), desc="Upserting to Qdrant"
        ):
            batch = jailbreak_prompts[i : i + BATCH]
            vecs = model.encode(batch).tolist()
            points = [
                rest.PointStruct(
                    id=str(uuid.uuid4()), vector=v, payload={"prompt": t}
                )
                for v, t in zip(vecs, batch)
            ]
            client.upsert(collection_name=_COLLECTION, points=points)


def cosine_similarity_score(prompt: str) -> float:
    _ensure_collection()
    vector = _get_model().encode(prompt).tolist()
    hits = _get_client().search(
        collection_name=_COLLECTION,
        query_vector=vector,
        limit=1
    )
    return hits[0].score if hits else 0.0
