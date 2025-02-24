import requests
import os
import re
import json
import PyPDF2
from pdfminer.high_level import extract_text
import pytesseract
from pdf2image import convert_from_path
from onedrive_organizer.config import OPENAI_API_KEY
from onedrive_organizer.database import insert_or_update_document_metadata, log_entry

CHATGPT_API_URL = "https://api.openai.com/v1/chat/completions"

def ocr_text_from_pdf(pdf_path):
    """ Nutzt OCR (Tesseract), um Text aus einem gescannten PDF zu extrahieren """
    try:
        images = convert_from_path(pdf_path)  # Konvertiert PDF-Seiten in Bilder
        text = "\n".join([pytesseract.image_to_string(img) for img in images])
        return text.strip()
    except Exception as e:
        log_entry("OCR_ERROR", f"❌ Fehler beim OCR-Scannen: {e}", "chatgpt_analysis.py")
        return ""

def extract_text_with_pdfminer(pdf_path):
    """ Versucht, Text mit pdfminer.six zu extrahieren """
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        log_entry("PDFMINER_ERROR", f"❌ Fehler bei pdfminer.six: {e}", "chatgpt_analysis.py")
        return ""

def extract_text_from_pdf(pdf_path):
    """ Versucht zuerst PyPDF2, dann pdfminer.six, dann OCR, um Text aus PDFs zu extrahieren """
    text = ""

    # 1️⃣ PyPDF2-Extraktion
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        log_entry("PYPDF2_ERROR", f"❌ Fehler bei PyPDF2: {e}", "chatgpt_analysis.py")

    # 2️⃣ pdfminer.six als Alternative
    if not text.strip():
        log_entry("TEXT_EXTRACTION", f"⚠️ Kein Text mit PyPDF2 gefunden, versuche pdfminer.six für {pdf_path}...", "chatgpt_analysis.py")
        text = extract_text_with_pdfminer(pdf_path)

    # 3️⃣ Falls pdfminer.six fehlschlägt → OCR
    if not text.strip():
        log_entry("TEXT_EXTRACTION", f"⚠️ Kein Text mit pdfminer.six gefunden, verwende OCR für {pdf_path}...", "chatgpt_analysis.py")
        text = ocr_text_from_pdf(pdf_path)

    return text.strip()

def extract_json_from_response(response_text):
    """ Extrahiert JSON aus einer OpenAI-Antwort und entfernt Erklärungen oder Markdown """
    try:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)  # Nur JSON extrahieren
        if json_match:
            return json.loads(json_match.group(0))
        else:
            log_entry("JSON_ERROR", f"⚠️ Kein gültiges JSON in Antwort: {response_text[:500]}", "chatgpt_analysis.py")
            return None
    except json.JSONDecodeError as e:
        log_entry("JSON_ERROR", f"❌ Fehler beim JSON-Parsing: {e}\nAntwort: {response_text[:500]}", "chatgpt_analysis.py")
        return None

def analyze_document_with_chatgpt(file_id, pdf_text):
    """ Sendet den Text eines PDFs an ChatGPT und speichert relevante Metadaten nur bei Erfolg """
    prompt = f"""
    Analysiere das folgende Dokument und extrahiere die relevanten Metadaten:
    
    1. Absender (Firma ohne Firmierung)
    2. Kategorie (z.B. Rentenversicherung, Unfallversicherung, Kontoauszug, Gebührenbescheid, Steuer)
    3. Dokumentdatum (falls vorhanden)
        
    Dokument:
    {pdf_text}

    **Gib die Antwort NUR im JSON-Format zurück, ohne Erklärungen oder zusätzlichen Text.**
    Beispiel:
    {{
        "sender": "Firma XYZ",
        "category": "Rechnung",
        "document_date": "2024-02-23"
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

    log_entry(file_id, "🔍 Starte ChatGPT-Analyse...", "chatgpt_analysis.py")

    response = requests.post(CHATGPT_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"].strip()

        metadata = extract_json_from_response(raw_content)

        if metadata:
            sender = metadata.get("sender", "").strip()
            category = metadata.get("category", "").strip()
            document_date = metadata.get("document_date", "").strip()

            # Nur speichern, wenn mindestens ein Feld gefüllt ist
            if sender or category or document_date:
                insert_or_update_document_metadata(file_id, sender, category, document_date)
                log_entry(file_id, f"✅ Metadaten gespeichert: Sender={sender}, Kategorie={category}, Datum={document_date}", "chatgpt_analysis.py")
            else:
                log_entry(file_id, "⚠️ Kein verwertbarer Inhalt extrahiert. Keine Speicherung.", "chatgpt_analysis.py")
        else:
            log_entry(file_id, "❌ Fehler: Keine verwertbaren Metadaten erhalten.", "chatgpt_analysis.py")
    else:
        log_entry(file_id, f"❌ Fehler bei API-Anfrage: {response.json()}", "chatgpt_analysis.py")
