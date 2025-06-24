from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    semantic_threshold: float = 0.42
    regex_patterns: list[str] = [
        r"(?i)reveal (?:the )?password",
        r"secret key",
        r"build a bomb",
        r"ignore (?:all )?prior instructions",
    ]
    audit_log_path: str = "logs/audit.log"  # ✅ Added this

settings = Settings()

