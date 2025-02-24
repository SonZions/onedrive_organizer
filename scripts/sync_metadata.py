import os
import sqlite3
from onedrive_organizer.database import initialize_db, download_db_from_onedrive, upload_db_to_onedrive, log_entry
from onedrive_organizer.drive import sync_metadata_from_folder, download_file
from onedrive_organizer.chatgpt_analysis import extract_text_from_pdf, analyze_document_with_chatgpt

# Sicherstellen, dass der 'temp/'-Ordner existiert
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

if __name__ == "__main__":
    initialize_db()  # Datenbank initialisieren (erst jetzt Log-Einträge möglich)
    log_entry("GLOBAL", "Starte Synchronisation...", "sync_metadata.py")

    # Datenbank von OneDrive herunterladen (falls vorhanden)
    download_db_from_onedrive()

    # Synchronisation starten (inkl. Unterordner)
    folders_to_sync = ["From_BrotherDevice", "Dokumente"]
    for folder in folders_to_sync:
        log_entry("GLOBAL", f"📂 Synchronisiere Dateien aus '{folder}' und Unterordner...", "sync_metadata.py")
        sync_metadata_from_folder(folder)  # Geht jetzt auch in Unterordner
        log_entry("GLOBAL", f"✅ Synchronisation für '{folder}' abgeschlossen.", "sync_metadata.py")

    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect("files_metadata.db")
    cursor = conn.cursor()

    # Rekursive Suche nach PDFs ohne Metadaten
    cursor.execute("""
        SELECT f.id, f.name FROM file_metadata f
        LEFT JOIN document_metadata d ON f.id = d.id
        WHERE f.mime_type = 'application/pdf' AND d.id IS NULL
    """)
    pdf_files = cursor.fetchall()
    conn.close()

    if not pdf_files:
        log_entry("GLOBAL", "✅ Keine neuen PDFs zur Analyse. Alles aktuell.", "sync_metadata.py")
    else:
        log_entry("GLOBAL", f"🔍 {len(pdf_files)} neue PDFs gefunden – Starte Analyse...", "sync_metadata.py")

        for file_id, file_name in pdf_files:
            try:
                local_pdf_path = os.path.join(TEMP_DIR, file_name)  # Temporärer Speicherort für das PDF
                download_file(file_id, local_pdf_path)  # PDF aus OneDrive herunterladen
                log_entry(file_id, "✅ Datei erfolgreich heruntergeladen.", "sync_metadata.py")

                pdf_text = extract_text_from_pdf(local_pdf_path)  # Text extrahieren
                if not pdf_text.strip():
                    log_entry(file_id, "⚠️ Kein Text extrahiert. Überspringe Analyse.", "sync_metadata.py")
                    continue

                analyze_document_with_chatgpt(file_id, pdf_text)  # ChatGPT-Analyse
                log_entry(file_id, "✅ ChatGPT-Analyse abgeschlossen.", "sync_metadata.py")

            except Exception as e:
                log_entry(file_id, f"❌ Fehler bei der Verarbeitung: {str(e)}", "sync_metadata.py")

    # Nach kompletter Verarbeitung Datenbank hochladen
    upload_db_to_onedrive()
    log_entry("GLOBAL", "✅ Synchronisation abgeschlossen. Datenbank hochgeladen.", "sync_metadata.py")
