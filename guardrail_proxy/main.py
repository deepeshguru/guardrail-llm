import os, time, httpx
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import List, Dict

from guardrail_proxy.decision import evaluate_prompt
from guardrail_proxy.audit import log
from guardrail_proxy.utils.role_context import get_user_role

BACKEND = os.getenv("LLM_BACKEND_URL", "http://127.0.0.1:8080/v1/chat/completions")

app = FastAPI(title="Guardrail Proxy (Final)")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., min_items=1)

class ChatResponse(BaseModel):
    response: Dict   # passthrough backend JSON

# --- echo upstream stub ---
def call_upstream_llm(prompt: str) -> str:
    return f"Echo: {prompt}"

@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok", "docs": "/docs"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, req: ChatRequest):
    user_role = get_user_role(request)

    prompt = req.messages[-1].content
    t0 = time.time()
    verdict = evaluate_prompt(prompt, role=user_role)
    latency_ms = round((time.time() - t0) * 1000, 2)

    if not verdict["allow"]:
        log({**verdict, "prompt": prompt, "latency_ms": latency_ms})
        raise HTTPException(
            status_code=403,
            detail={"error": "Prompt blocked", **verdict},
        )

    upstream_resp = call_upstream_llm(prompt)
    log(
        {
            'prompt': prompt,
            'response': upstream_resp,
            'verdict': verdict,
            "latency_ms": latency_ms,
            }
        )

    return ChatResponse(response={"content": upstream_resp})
