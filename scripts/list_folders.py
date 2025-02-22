import requests
from onedrive_organizer.auth import get_access_token
from onedrive_organizer.config import GRAPH_API_URL

def list_onedrive_folders():
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(f"{GRAPH_API_URL}/root/children", headers=headers)

    if response.status_code == 200:
        print("\n📂 Verfügbare OneDrive-Ordner:")
        for item in response.json().get("value", []):
            if "folder" in item:
                print(f"- {item['name']} (ID: {item['id']})")
    else:
        print("❌ Fehler beim Abrufen der Ordner:", response.json())

if __name__ == "__main__":
    list_onedrive_folders()
