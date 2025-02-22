import requests
from onedrive_organizer.auth import get_access_token
from onedrive_organizer.config import GRAPH_API_URL
from onedrive_organizer.database import insert_or_update_file

def get_folder_id(folder_name):
    """ Holt die ID eines OneDrive-Ordners anhand seines Namens """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/root/children", headers=headers)

    if response.status_code == 200:
        for item in response.json().get("value", []):
            if item["name"] == folder_name and "folder" in item:
                return item["id"]
    return None

def sync_metadata_from_folder(folder_name):
    """ Ruft Metadaten aus einem bestimmten OneDrive-Ordner ab und speichert sie in SQLite """
    folder_id = get_folder_id(folder_name)
    if not folder_id:
        print(f"❌ Der Ordner '{folder_name}' wurde nicht gefunden.")
        return

    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/items/{folder_id}/children", headers=headers)

    if response.status_code == 200:
        files = response.json().get("value", [])
        print(f"\n🔄 Synchronisiere Dateien aus '{folder_name}'...")

        for file in files:
            file_metadata = {
                "id": file["id"],
                "name": file["name"],
                "created_datetime": file.get("createdDateTime", "Unbekannt"),
                "modified_datetime": file.get("lastModifiedDateTime", "Unbekannt"),
                "size": file.get("size", 0),
                "mime_type": file.get("file", {}).get("mimeType", "Unbekannt"),
                "parent_folder": folder_name
            }
            insert_or_update_file(file_metadata)

        print(f"✅ Synchronisation für '{folder_name}' abgeschlossen.")

    else:
        print("❌ Fehler beim Abrufen der Dateien:", response.json())

def download_file(file_id, local_path):
    """ Lädt eine Datei aus OneDrive herunter """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/items/{file_id}/content", headers=headers, stream=True)

    if response.status_code == 200:
        with open(local_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"✅ Datei {local_path} erfolgreich heruntergeladen.")
    else:
        print(f"❌ Fehler beim Herunterladen von Datei {file_id}: {response.json()}")