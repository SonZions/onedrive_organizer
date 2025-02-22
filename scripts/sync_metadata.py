import sqlite3  # Wichtig: SQLite importieren
from onedrive_organizer.database import initialize_db, download_db_from_onedrive, upload_db_to_onedrive
from onedrive_organizer.drive import sync_metadata_from_folder, download_file
from onedrive_organizer.chatgpt_analysis import extract_text_from_pdf, analyze_document_with_chatgpt

if __name__ == "__main__":
    # Datenbank von OneDrive herunterladen (falls vorhanden)
    download_db_from_onedrive()

    # Datenbank initialisieren (falls sie noch nicht existiert)
    initialize_db()

    # Synchronisation starten
    folders_to_sync = ["From_BrotherDevice", "Dokumente"]
    for folder in folders_to_sync:
        sync_metadata_from_folder(folder)

    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect("files_metadata.db")
    cursor = conn.cursor()

    # Abrufen aller PDFs, die noch KEINE Metadaten haben
    cursor.execute("""
        SELECT f.id, f.name FROM file_metadata f
        LEFT JOIN document_metadata d ON f.id = d.id
        WHERE f.mime_type = 'application/pdf' AND d.id IS NULL
    """)
    pdf_files = cursor.fetchall()
    conn.close()

    # Falls es keine neuen PDFs gibt, beenden
    if not pdf_files:
        print("✅ Keine neuen PDFs zur Analyse. Alles auf dem aktuellen Stand.")
    else:
        print(f"🔍 {len(pdf_files)} neue PDFs gefunden – Senden an ChatGPT...")

        for file_id, file_name in pdf_files:
            local_pdf_path = f"temp/{file_name}"  # Temporärer Speicherort für das PDF
            download_file(file_id, local_pdf_path)  # PDF aus OneDrive herunterladen
            pdf_text = extract_text_from_pdf(local_pdf_path)  # Text extrahieren
            analyze_document_with_chatgpt(file_id, pdf_text)  # ChatGPT-Analyse

    # Nach kompletter Verarbeitung Datenbank hochladen
    upload_db_to_onedrive()
