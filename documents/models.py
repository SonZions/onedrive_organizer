from django.db import models

class FileMetadata(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=500)
    created_datetime = models.DateTimeField()
    modified_datetime = models.DateTimeField()
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=255)
    parent_folder = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class DocumentMetadata(models.Model):
    file = models.OneToOneField(FileMetadata, on_delete=models.CASCADE)
    sender = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    document_date = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.file.name} - {self.category}"

