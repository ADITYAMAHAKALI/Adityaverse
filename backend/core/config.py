import os
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()

class Settings:
    project_name = "Research Connect"
    secret_key = os.getenv("SECRET_KEY", "change-me")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    # DB
    database_url = os.getenv("DATABASE_URL")

    # Google OAuth
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    # Optional: validate things here if needed
    def validate(self):
        missing = [
            key for key in [
                "SECRET_KEY", "DATABASE_URL", "GOOGLE_CLIENT_ID",
                "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"
            ] if os.getenv(key) is None
        ]
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")

# ✅ Singleton instance
settings = Settings()
settings.validate()  # Optional: fail-fast if anything is missing
