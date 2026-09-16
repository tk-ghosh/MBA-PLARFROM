from django.urls import path

from . import views

urlpatterns = [
    path('upload-converter/', views.upload_converter_view, name='upload_converter'),
    path('upload-converter/download/<str:token>/', views.download_generated_file, name='download_generated_file'),
]