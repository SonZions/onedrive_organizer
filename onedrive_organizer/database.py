import sqlite3
import requests
import os
import time
import os
import inspect
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

    # Tabelle für ChatGPT-extrahierte Dokument-Metadaten
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_metadata (
            id TEXT PRIMARY KEY,
            sender TEXT,
            category TEXT,
            document_date TEXT,
            FOREIGN KEY(id) REFERENCES file_metadata(id)
        )
    """)

    # NEUE Log-Tabelle für Fehler, Warnungen & Prozessinfos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_data (
            id TEXT,
            timestamp TEXT,
            process TEXT,
            message TEXT,
            PRIMARY KEY (id, timestamp)
        )
    """)

    conn.commit()
    conn.close()

def log_entry(file_id, message, process=None):
    """ Speichert einen Log-Eintrag mit Timestamp (Hundertstelsekunden) """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(time.time() * 100) % 100:02d}"
    process_name = process or inspect.stack()[1].filename.split(os.sep)[-1]  # Modulname als Prozessname
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO log_data (id, timestamp, process, message)
        VALUES (?, ?, ?, ?)
    """, (file_id, timestamp, process_name, message))
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