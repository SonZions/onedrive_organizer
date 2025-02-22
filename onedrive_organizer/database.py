import sqlite3
from onedrive_organizer.config import DB_FILE

def initialize_db():
    """ Erstellt die SQLite-Datenbank und Tabelle, falls nicht vorhanden """
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
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
