from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .decision import evaluate_prompt
from .audit import log
app = FastAPI(title="Guardrail Proxy (Mid‑Semester)")

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

# --- echo upstream stub ---
def call_upstream_llm(prompt: str) -> str:
    return f"Echo: {prompt}"

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    verdict = evaluate_prompt(req.prompt)
    if not verdict["allow"]:
        log({'prompt': req.prompt, 'response': '', 'verdict': verdict})
        raise HTTPException(status_code=403, detail={"error": "Prompt blocked", **verdict})

    # else pass through
    upstream_resp = call_upstream_llm(req.prompt)
    log({'prompt': req.prompt, 'response': upstream_resp, 'verdict': verdict})
    return ChatResponse(response=upstream_resp)
