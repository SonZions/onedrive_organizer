import sqlite3
import requests
import os
from onedrive_organizer.config import LOCAL_DB_FILE, ONEDRIVE_DB_PATH, GRAPH_API_URL
from onedrive_organizer.auth import get_access_token

def initialize_db():
    """ Erstellt die SQLite-Datenbank und Tabelle, falls nicht vorhanden """
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_metadata (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_datetime TEXT,
            modified_datetime TEXT,
            size INTEGER,
            mime_type TEXT,
            parent_folder TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_or_update_file(file_metadata):
    """ Fügt eine Datei in die Datenbank ein oder aktualisiert sie """
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO file_metadata (id, name, created_datetime, modified_datetime, size, mime_type, parent_folder)
        VALUES (:id, :name, :created_datetime, :modified_datetime, :size, :mime_type, :parent_folder)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            created_datetime=excluded.created_datetime,
            modified_datetime=excluded.modified_datetime,
            size=excluded.size,
            mime_type=excluded.mime_type,
            parent_folder=excluded.parent_folder
    """, file_metadata)
    conn.commit()
    conn.close()

    # Nach jeder Änderung Datei in OneDrive hochladen
    upload_db_to_onedrive()

def upload_db_to_onedrive():
    """ Lädt die SQLite-Datenbank nach OneDrive hoch """
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/octet-stream"
    }

    with open(LOCAL_DB_FILE, "rb") as file_data:
        response = requests.put(
            f"{GRAPH_API_URL}/root:{ONEDRIVE_DB_PATH}:/content",
            headers=headers,
            data=file_data
        )

    if response.status_code in [200, 201]:
        print("✅ Datenbank erfolgreich nach OneDrive hochgeladen.")
    else:
        print("❌ Fehler beim Hochladen der Datenbank:", response.json())

def download_db_from_onedrive():
    """ Lädt die SQLite-Datenbank von OneDrive herunter """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/root:{ONEDRIVE_DB_PATH}:/content", headers=headers)

    if response.status_code == 200:
        with open(LOCAL_DB_FILE, "wb") as file:
            file.write(response.content)
        print("✅ Datenbank erfolgreich von OneDrive heruntergeladen.")
    else:
        print("❌ Keine bestehende Datenbank in OneDrive gefunden. Eine neue wird erstellt.")
        initialize_db()
