import requests
import os
import re
import PyPDF2
from pdfminer.high_level import extract_text
import pytesseract
from pdf2image import convert_from_path
from onedrive_organizer.config import OPENAI_API_KEY
from onedrive_organizer.database import insert_or_update_document_metadata
import json

CHATGPT_API_URL = "https://api.openai.com/v1/chat/completions"

def ocr_text_from_pdf(pdf_path):
    """ Nutzt OCR (Tesseract), um Text aus einem gescannten PDF zu extrahieren """
    try:
        images = convert_from_path(pdf_path)  # Konvertiert PDF-Seiten in Bilder
        text = "\n".join([pytesseract.image_to_string(img) for img in images])
        return text.strip()
    except Exception as e:
        print(f"❌ Fehler beim OCR-Scannen von {pdf_path}: {e}")
        return ""

def extract_text_with_pdfminer(pdf_path):
    """ Versucht, Text mit pdfminer.six zu extrahieren """
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"❌ Fehler beim Extrahieren von Text mit pdfminer.six aus {pdf_path}: {e}")
        return ""


def extract_text_from_pdf(pdf_path):
    """ Versucht zuerst PyPDF2, dann pdfminer.six, dann OCR, um Text aus PDFs zu extrahieren """
    text = ""

    # 1️⃣ Versuche mit PyPDF2
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        print(f"❌ Fehler beim Extrahieren von Text mit PyPDF2 aus {pdf_path}: {e}")

    # 2️⃣ Falls kein Text gefunden wurde, versuche pdfminer.six
    if not text.strip():
        print(f"⚠️ Kein Text mit PyPDF2 gefunden, versuche pdfminer.six für {pdf_path}...")
        text = extract_text_with_pdfminer(pdf_path)

    # 3️⃣ Falls immer noch kein Text gefunden wurde, verwende OCR
    if not text.strip():
        print(f"⚠️ Kein Text mit pdfminer.six gefunden, verwende OCR für {pdf_path}...")
        text = ocr_text_from_pdf(pdf_path)

    return text.strip()

def extract_json_from_response(response_text):
    """ Extrahiert JSON aus einer OpenAI-Antwort und entfernt Erklärungen oder Markdown """
    try:
        # Falls die Antwort Markdown-Format enthält, entfernen
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))  # Nur den JSON-Teil parsen
        else:
            print(f"❌ Kein gültiges JSON in der Antwort gefunden: {response_text[:500]}")
            return None
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim JSON-Parsing: {e}\nAntwort: {response_text[:500]}")
        return None

def analyze_document_with_chatgpt(file_id, pdf_text):
    """ Sendet den Text eines PDFs an ChatGPT und extrahiert relevante Metadaten """
    prompt = f"""
    Analysiere das folgende Dokument und extrahiere die relevanten Metadaten:

    1. Absender (Firma ohne Firmierung)
    2. Kategorie (z.B. Rentenversicherung, Unfallversicherung, Kontoauszug, Gebührenbescheid, Steuer)
    3. Dokumentdatum (falls vorhanden)
    
    Dokument:
    {pdf_text}

    **Gib NUR die JSON-Antwort zurück, ohne Erklärungen oder zusätzlichen Text.**  
    Format:
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
        "model": "gpt-4o-mini",  # Falls gpt-4 nicht verfügbar ist, nutze "gpt-3.5-turbo"
        "messages": [{"role": "system", "content": "Du bist ein intelligenter Dokumentenanalyse-Experte."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(CHATGPT_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"].strip()

        # JSON aus der OpenAI-Antwort extrahieren
        metadata = extract_json_from_response(raw_content)

        if metadata:
            insert_or_update_document_metadata(
                file_id,
                metadata.get("sender", "Unbekannt"),
                metadata.get("category", "Unbekannt"),
                metadata.get("document_date", "Unbekannt")
            )
            print(f"✅ Metadaten für {file_id} gespeichert: {metadata}")
        else:
            print(f"❌ Konnte keine validen Metadaten für Datei {file_id} extrahieren.")
    else:
        print(f"❌ Fehler bei der API-Anfrage: {response.json()}")