import os
import requests
from onedrive_organizer.auth import get_access_token
from onedrive_organizer.config import GRAPH_API_URL
from onedrive_organizer.database import insert_or_update_file, log_entry

def get_folder_id(folder_name):
    """ Holt die ID eines OneDrive-Ordners anhand seines Namens """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/root/children", headers=headers)

    if response.status_code == 200:
        for item in response.json().get("value", []):
            if item["name"] == folder_name and "folder" in item:
                return item["id"]
    log_entry("GLOBAL", f"❌ Ordner '{folder_name}' nicht gefunden.", "drive.py")
    return None

def sync_metadata_from_folder(folder_name):
    """ Ruft Metadaten aus einem bestimmten OneDrive-Ordner (inkl. Unterordner) ab und speichert sie in SQLite """
    log_entry("GLOBAL", f"🔄 Synchronisiere Dateien aus '{folder_name}' (inkl. Unterordner)...", "drive.py")
    
    folder_id = get_folder_id(folder_name)
    if not folder_id:
        log_entry("GLOBAL", f"❌ Der Ordner '{folder_name}' wurde nicht gefunden.", "drive.py")
        return

    sync_folder_recursive(folder_id, folder_name)

def sync_folder_recursive(folder_id, current_path):
    """ Rekursive Verarbeitung von Dateien und Unterordnern in OneDrive """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/items/{folder_id}/children", headers=headers)

    if response.status_code == 200:
        items = response.json().get("value", [])
        
        if not items:
            log_entry("GLOBAL", f"⚠️ Keine Dateien in '{current_path}' gefunden.", "drive.py")
            return

        for item in items:
            if "folder" in item:  # Falls es ein Unterordner ist
                subfolder_id = item["id"]
                subfolder_name = item["name"]
                new_path = os.path.join(current_path, subfolder_name)

                log_entry("GLOBAL", f"📂 Wechsle in Unterordner '{new_path}'...", "drive.py")
                sync_folder_recursive(subfolder_id, new_path)  # Rekursiver Aufruf
            
            else:  # Falls es eine Datei ist
                file_metadata = {
                    "id": item["id"],
                    "name": item["name"],
                    "created_datetime": item.get("createdDateTime", "Unbekannt"),
                    "modified_datetime": item.get("lastModifiedDateTime", "Unbekannt"),
                    "size": item.get("size", 0),
                    "mime_type": item.get("file", {}).get("mimeType", "Unbekannt"),
                    "parent_folder": current_path
                }
                insert_or_update_file(file_metadata)
                log_entry(item["id"], f"✅ Datei '{item['name']}' synchronisiert aus '{current_path}'.", "drive.py")

    else:
        log_entry("GLOBAL", f"❌ Fehler beim Abrufen von Dateien in '{current_path}': {response.json()}", "drive.py")

def download_file(file_id, local_path):
    """ Lädt eine Datei aus OneDrive herunter und speichert sie lokal """
    local_dir = os.path.dirname(local_path)
    if local_dir and not os.path.exists(local_dir):
        os.makedirs(local_dir)

    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/items/{file_id}/content", headers=headers, stream=True)

    if response.status_code == 200:
        with open(local_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        log_entry(file_id, f"✅ Datei erfolgreich heruntergeladen: {local_path}", "drive.py")
    else:
        log_entry(file_id, f"❌ Fehler beim Herunterladen: {response.json()}", "drive.py")
