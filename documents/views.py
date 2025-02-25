import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import FileMetadata, DocumentMetadata
from onedrive_organizer.drive import download_file as onedrive_download_file
from onedrive_organizer.chatgpt_analysis import analyze_document_with_chatgpt
from onedrive_organizer.database import insert_or_update_document_metadata
from onedrive_organizer.config import DB_PATH

# Home: Zeigt alle Dateien & Metadaten als interaktiven Baum
def index(request):
    files = FileMetadata.objects.all()
    return render(request, "index.html", {"files": files})

# Dateien ohne Metadaten anzeigen
def missing_metadata(request):
    files = FileMetadata.objects.filter(documentmetadata=None)
    return render(request, "missing_metadata.html", {"files": files})

# Einzelne Datei-Analyse starten
@csrf_exempt
def analyze_file(request, file_id):
    file = get_object_or_404(FileMetadata, id=file_id)
    local_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    
    # Datei aus OneDrive herunterladen, falls nicht vorhanden
    if not default_storage.exists(local_file_path):
        onedrive_download_file(file_id, local_file_path)
    
    with open(local_file_path, "rb") as f:
        text = analyze_document_with_chatgpt(f.read())
    
    # Metadaten in DB speichern
    insert_or_update_document_metadata(
        file_id,
        text.get("sender", "Unbekannt"),
        text.get("category", "Unbekannt"),
        text.get("document_date", "Unbekannt")
    )
    
    return JsonResponse({"message": "Analyse abgeschlossen", "data": text})

# Datei-Download
def download_file(request, file_id):
    file = get_object_or_404(FileMetadata, id=file_id)
    local_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    
    # Datei aus OneDrive herunterladen, falls nicht vorhanden
    if not default_storage.exists(local_file_path):
        onedrive_download_file(file_id, local_file_path)
    
    return FileResponse(open(local_file_path, "rb"), as_attachment=True, filename=file.name)

# Datenbankverbindung für files_metadata.db sicherstellen
import sqlite3

def get_db_connection():
    return sqlite3.connect(LOCAL_DB_FILE)
