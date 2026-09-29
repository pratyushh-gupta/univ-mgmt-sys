import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Resolve the backend's .env independently of the process working directory.
BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(BACKEND_ENV_FILE, override=False)

DEVELOPMENT_JWT_SECRET = "dev-only-change-me"
PLACEHOLDER_JWT_SECRETS = {
    "change-me",
    "change-this-in-production",
    "dev-only-change-me",
    "replace-me",
    "replace-with-a-random-secret-of-at-least-32-characters",
    "your-secret-key",
    "your-secret-here",
}

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./university.db")
    jwt_secret: str = field(init=False)
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    environment: str = os.getenv("ENVIRONMENT", "development").strip().lower()
    cors_origins: list[str] = field(default_factory=lambda: [
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if value.strip()
    ])

    def __post_init__(self):
        configured_secret = os.getenv("JWT_SECRET", "").strip()
        if self.environment == "production":
            if (
                not configured_secret
                or configured_secret.lower() in PLACEHOLDER_JWT_SECRETS
                or configured_secret == DEVELOPMENT_JWT_SECRET
                or len(configured_secret) < 32
            ):
                raise RuntimeError(
                    "Production requires an explicit JWT_SECRET of at least 32 characters; "
                    "development and placeholder secrets are not allowed"
                )
            resolved_secret = configured_secret
        else:
            resolved_secret = (
                configured_secret
                or os.getenv("SECRET_KEY", "").strip()
                or DEVELOPMENT_JWT_SECRET
            )
        object.__setattr__(self, "jwt_secret", resolved_secret)

settings = Settings()
