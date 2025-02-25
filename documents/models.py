from django.db import models

class FileMetadata(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=500)
    created_datetime = models.TextField()
    modified_datetime = models.TextField()
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=255)
    parent_folder = models.CharField(max_length=500)

    class Meta:
        db_table = "file_metadata"  # Weist Django an, die bestehende Tabelle zu verwenden

class DocumentMetadata(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    sender = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    document_date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "document_metadata"  # Bestehende Tabelle nutzen
