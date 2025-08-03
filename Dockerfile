
# --- Dev image for mid‑sem proxy ---
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
CMD ["uvicorn", "guardrail_proxy.main:app", "--host", "0.0.0.0", "--port", "8000"]
