from onedrive_organizer.database import initialize_db
from onedrive_organizer.drive import sync_metadata_from_folder

if __name__ == "__main__":
    # Datenbank initialisieren
    initialize_db()

    # Synchronisation starten
    folders_to_sync = ["From_BrotherDevice", "Dokumente"]
    for folder in folders_to_sync:
        sync_metadata_from_folder(folder)
