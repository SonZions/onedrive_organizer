from django.shortcuts import render, get_object_or_404
from onedrive_organizer.drive import download_file as onedrive_download_file
from .models import FileMetadata, DocumentMetadata
import os
from django.conf import settings
from django.http import FileResponse
import json

from django.db import connection
from django.shortcuts import render



def index(request):
    """ Holt die Dateien aus der Datenbank und organisiert sie für die Baumstruktur """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT f.id, f.name, f.created_datetime, f.size, f.mime_type, 
                   d.sender, d.category, d.document_date
            FROM file_metadata f
            LEFT JOIN document_metadata d ON f.id = d.id
        """)
        rows = cursor.fetchall()

    # Daten in ein Dictionary umwandeln
    files = [
        {
            "id": row[0],
            "name": row[1],
            "created_datetime": row[2],
            "size": row[3],
            "mime_type": row[4],
            "sender": row[5] if row[5] else "Unbekannt",
            "category": row[6] if row[6] else "Unbekannt",
            "document_date": row[7] if row[7] else "Unbekannt",
        }
        for row in rows
    ]
    
    tree_structure = {}
    for file in files:
        category = file.documentmetadata.category if file.documentmetadata else "Unbekannt"
        sender = file.documentmetadata.sender if file.documentmetadata else "Unbekannt"
        year = file.created_datetime.year

        if category not in tree_structure:
            tree_structure[category] = {}

        if sender not in tree_structure[category]:
            tree_structure[category][sender] = {}

        if year not in tree_structure[category][sender]:
            tree_structure[category][sender][year] = []

        tree_structure[category][sender][year].append(file)

    print(json.dumps(tree_structure, indent=4, default=str))
    return render(request, "documents/index.html", {"tree_structure": tree_structure})


def download(request, file_id):
    """ Lädt die Datei aus OneDrive herunter und gibt sie zum Download zurück """
    file = get_object_or_404(FileMetadata, id=file_id)
    local_path = os.path.join(settings.MEDIA_ROOT, file.name)

    # Falls die Datei nicht lokal vorhanden ist, aus OneDrive laden
    if not os.path.exists(local_path):
        onedrive_download_file(file_id, local_path)

    return FileResponse(open(local_path, "rb"), as_attachment=True, filename=file.name)
