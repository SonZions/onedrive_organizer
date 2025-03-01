from django.shortcuts import render, get_object_or_404
from onedrive_organizer.drive import download_file as onedrive_download_file
from .models import FileMetadata, DocumentMetadata
import os
from django.conf import settings
from django.http import FileResponse, HttpResponse
import json
from django.db import connection
from collections import defaultdict



def index(request):
      # SQL-Abfrage, um die Daten aus `file_metadata` und `document_metadata` zusammenzuführen
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT f.id, f.name, f.created_datetime, f.size, f.mime_type, 
                   d.sender, d.category, d.document_date
            FROM file_metadata f
            INNER JOIN document_metadata d ON f.id = d.id
            ORDER BY d.category
            LIMIT 10
        """)
        rows = cursor.fetchall()

    # Struktur für den Baum initialisieren
    tree_structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # Daten in die Baumstruktur einsortieren
    for row in rows:
        file_id, name, created_datetime, size, mime_type, sender, category, document_date = row
        
        category = category or "Unbekannt"
        sender = sender or "Unbekannt"
        
        # Jahr aus `document_date` extrahieren, wenn möglich
        year = "Unbekannt"
        if document_date and len(document_date) >= 4:
            year = document_date[:4]  # Die ersten 4 Zeichen als Jahr nehmen

        # Datei zur Baumstruktur hinzufügen
        tree_structure[category][sender][year].append({
            "id": file_id,
            "name": name,
            "size": size
        })
        print(tree_structure)

        print("===== TREE STRUCTURE DEBUG =====")
        for category, senders in tree_structure.items():
            print(f"Kategorie: {category}")
            for sender, years in senders.items():
                print(f"  Sender: {sender}")
                for year, files in years.items():
                    print(f"    Jahr: {year} - {len(files)} Dateien")
        print("===== END DEBUG =====")


    return render(request, "documents/index.html", {"tree_structure": dict(tree_structure)})


def download(request, file_id):
    """ Lädt die Datei aus OneDrive herunter und gibt sie zum Download zurück """
    file = get_object_or_404(FileMetadata, id=file_id)
    local_path = os.path.join(settings.MEDIA_ROOT, file.name)

    # Falls die Datei nicht lokal vorhanden ist, aus OneDrive laden
    if not os.path.exists(local_path):
        onedrive_download_file(file_id, local_path)

    return FileResponse(open(local_path, "rb"), as_attachment=True, filename=file.name)


def debug_tree(request):
    from .views import build_tree_structure  # Importiere die Tree-Funktion
    return HttpResponse(json.dumps(build_tree_structure(), indent=4), content_type="application/json")
