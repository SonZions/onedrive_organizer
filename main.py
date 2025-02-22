from onedrive_organizer.sync_metadata import sync_metadata_from_folder

if __name__ == "__main__":
    folders = ["From_BrotherDevice", "Dokumente"]
    for folder in folders:
        sync_metadata_from_folder(folder)
