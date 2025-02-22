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
