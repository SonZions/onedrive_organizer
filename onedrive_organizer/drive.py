import requests
from onedrive_organizer.auth import get_access_token
from onedrive_organizer.config import GRAPH_API_URL

def get_folder_id(folder_name):
    """ Holt die ID eines OneDrive-Ordners anhand seines Namens """
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/root/children", headers=headers)

    if response.status_code == 200:
        for item in response.json().get("value", []):
            if item["name"] == folder_name and "folder" in item:
                return item["id"]
    return None

def list_files_in_folder(folder_name):
    """ Listet alle Dateien und ihr Erstellungsdatum in einem OneDrive-Ordner """
    folder_id = get_folder_id(folder_name)
    if not folder_id:
        print(f"❌ Der Ordner '{folder_name}' wurde nicht gefunden.")
        return

    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/items/{folder_id}/children", headers=headers)

    if response.status_code == 200:
        files = response.json().get("value", [])
        print(f"\n📂 Dateien in '{folder_name}':")
        for file in files:
            created_time = file.get("createdDateTime", "Unbekannt")
            print(f"- {file['name']} (Erstellt: {created_time})")
    else:
        print("Fehler beim Abrufen der Dateien:", response.json())
