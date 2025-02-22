import sqlite3
import requests
import os
from onedrive_organizer.config import LOCAL_DB_FILE, ONEDRIVE_DB_PATH, GRAPH_API_URL
from onedrive_organizer.auth import get_access_token

def initialize_db():
    """ Erstellt die SQLite-Datenbank und Tabellen, falls sie nicht existieren """
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()

    # Tabelle für allgemeine Datei-Metadaten
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

    # Neue Tabelle für ChatGPT-extrahierte Dokument-Metadaten
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_metadata (
            id TEXT PRIMARY KEY,
            sender TEXT,
            category TEXT,
            document_date TEXT,
            FOREIGN KEY(id) REFERENCES file_metadata(id)
        )
    """)

    conn.commit()
    conn.close()

def insert_or_update_document_metadata(file_id, sender, category, document_date):
    """ Fügt extrahierte Metadaten eines Dokuments in die Datenbank ein oder aktualisiert sie """
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO document_metadata (id, sender, category, document_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            sender=excluded.sender,
            category=excluded.category,
            document_date=excluded.document_date
    """, (file_id, sender, category, document_date))
    conn.commit()
    conn.close()

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
