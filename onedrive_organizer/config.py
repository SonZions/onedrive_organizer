import os
from dotenv import load_dotenv

# .env-Datei laden
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID", "common")
SCOPES = ["Files.ReadWrite"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/drive"
LOCAL_DB_FILE = "files_metadata.db"  # Lokale SQLite-Datei
ONEDRIVE_DB_PATH = "/files_metadata.db"  # Zielpfad in OneDrive
