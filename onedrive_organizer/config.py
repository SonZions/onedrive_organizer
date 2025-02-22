import os
from dotenv import load_dotenv

# .env-Datei laden
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID", "common")
SCOPES = ["Files.ReadWrite"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/drive"

# Lokale und OneDrive-Pfade für die SQLite-Datenbank
LOCAL_DB_FILE = "files_metadata.db"  # Lokale Kopie
ONEDRIVE_DB_PATH = "/files_metadata.db"  # Zielpfad in OneDrive

# Token-Datei für Authentifizierung
TOKEN_FILE = "token.json"

# OpenAI API Key (für ChatGPT-Anfragen)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
