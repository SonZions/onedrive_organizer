from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("missing-metadata/", views.missing_metadata, name="missing_metadata"),
    path("analyze/<str:file_id>/", views.analyze_file, name="analyze_file"),
    path("download/<str:file_id>/", views.download_file, name="download_file"),
]

