from django.shortcuts import render, get_object_or_404
from onedrive_organizer.drive import download_file as onedrive_download_file
from .models import FileMetadata, DocumentMetadata
import os
from django.conf import settings
from django.http import FileResponse

def index(request):
    """ Holt die Dateien aus der Datenbank und organisiert sie für die Baumstruktur """
    files = FileMetadata.objects.all().select_related('documentmetadata')

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

    return render(request, "documents/index.html", {"tree_structure": tree_structure})


def download(request, file_id):
    """ Lädt die Datei aus OneDrive herunter und gibt sie zum Download zurück """
    file = get_object_or_404(FileMetadata, id=file_id)
    local_path = os.path.join(settings.MEDIA_ROOT, file.name)

    # Falls die Datei nicht lokal vorhanden ist, aus OneDrive laden
    if not os.path.exists(local_path):
        onedrive_download_file(file_id, local_path)

    return FileResponse(open(local_path, "rb"), as_attachment=True, filename=file.name)
