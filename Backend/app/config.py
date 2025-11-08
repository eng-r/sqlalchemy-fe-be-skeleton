from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASS: str = os.getenv("DB_PASS", "admin")  # <-- set yours
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3307")
    DB_NAME: str = os.getenv("DB_NAME", "employees")
    CORS_ORIGINS: list[str] = [os.getenv("CORS_ORIGIN", "*")]
    SECRETS_FILE: str = os.getenv("SECRETS_FILE", "secrets/secrets.json")


def _ensure_path_is_absolute(path: str) -> str:
    if os.path.isabs(path):
        return path
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, path)


settings = Settings()
settings.SECRETS_FILE = _ensure_path_is_absolute(settings.SECRETS_FILE)
