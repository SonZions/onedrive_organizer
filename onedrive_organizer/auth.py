import json
import os
import msal
from onedrive_organizer.config import CLIENT_ID, AUTHORITY, SCOPES, TOKEN_FILE

def save_token(token_data):
    """ Speichert das Token in einer Datei """
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def load_token():
    """ Lädt das gespeicherte Token, falls vorhanden """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def get_access_token():
    """ Holt das OneDrive Access-Token über MSAL """
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    token_result = load_token()
    if token_result and "access_token" in token_result:
        return token_result["access_token"]

    print("Starte Device Code Flow für Login...")
    flow = app.initiate_device_flow(SCOPES)
    if "message" in flow:
        print(flow["message"])
    else:
        raise Exception("Fehler beim Start des Device Code Flows.")

    token_result = app.acquire_token_by_device_flow(flow)
    if "access_token" in token_result:
        save_token(token_result)
        return token_result["access_token"]
    else:
        raise Exception(f"Fehler beim Abrufen des Tokens: {token_result.get('error_description')}")
