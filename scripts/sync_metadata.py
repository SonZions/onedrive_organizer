from onedrive_organizer.database import initialize_db, download_db_from_onedrive, upload_db_to_onedrive
from onedrive_organizer.drive import sync_metadata_from_folder

if __name__ == "__main__":
    # Datenbank von OneDrive herunterladen (falls vorhanden)
    download_db_from_onedrive()

    # Datenbank initialisieren (falls sie noch nicht existiert)
    initialize_db()

    # Synchronisation starten
    folders_to_sync = ["From_BrotherDevice", "Dokumente"]
    for folder in folders_to_sync:
        sync_metadata_from_folder(folder)

    # Nach der gesamten Synchronisation die Datenbank einmal hochladen
    upload_db_to_onedrive()
