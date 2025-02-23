import requests
import os
import PyPDF2
from onedrive_organizer.config import OPENAI_API_KEY
from onedrive_organizer.database import insert_or_update_document_metadata
import json

CHATGPT_API_URL = "https://api.openai.com/v1/chat/completions"

def extract_text_from_pdf(pdf_path):
    """ Extrahiert reinen Text aus einer PDF-Datei """
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

def analyze_document_with_chatgpt(file_id, pdf_text):
    """ Sendet den Text eines PDFs an ChatGPT und extrahiert relevante Metadaten """
    prompt = f"""
    Analysiere das folgende Dokument und extrahiere die relevanten Metadaten:
    
    1. Absender (Firma ohne Firmierung)
    2. Kategorie (Rentenversicherung, Unfallversicherung, Kontoauszug, Gebührenbescheid, Steuer, etc.)
    3. Dokumentdatum (falls vorhanden)

    Dokument:
    {pdf_text}

    Gib die Antwort im JSON-Format aus:
    {{
        "sender": "...",
        "category": "...",
        "document_date": "..."
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "Du bist ein intelligenter Dokumentenanalyse-Experte."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(CHATGPT_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        try:
            response_data = response.json()
            metadata = response_data["choices"][0]["message"]["content"]
            try:
                metadata = json.loads(metadata)  # Sicheres JSON-Parsing
                insert_or_update_document_metadata(file_id, metadata["sender"], metadata["category"], metadata["document_date"])
                print(f"✅ Metadaten für {file_id} gespeichert: {metadata}")
            except json.JSONDecodeError:
                print(f"❌ Fehler beim Parsen der API-Antwort für Datei {file_id}: {metadata}")
            except KeyError:
                print(f"❌ API-Antwort unvollständig für Datei {file_id}: {metadata}")
            insert_or_update_document_metadata(file_id, metadata["sender"], metadata["category"], metadata["document_date"])
            print(f"✅ Metadaten für {file_id} gespeichert: {metadata}")
        except Exception as e:
            print(f"❌ Fehler bei der Verarbeitung der ChatGPT-Antwort: {e}")
    else:
        print(f"❌ Fehler bei der API-Anfrage: {response.json()}")

