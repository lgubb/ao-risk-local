import os
from dotenv import load_dotenv

# Load variables from a local .env file (useful in dev). In prod, rely on real env.
load_dotenv()

# Security & auth settings
# IMPORTANT: Set SECRET_KEY via environment in production.
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-dev")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Toggle d'authentification (par défaut désactivée pour vitrine)
# Mettre AUTH_REQUIRED=true dans l'env pour activer la protection des routes sensibles
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
