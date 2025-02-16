from django.urls import path
from . import views

app_name = 'parsing'

urlpatterns = [
    # Add a URL pattern for your HTML-based parsing view:
    path('parse-references-html/', views.parse_references_html, name='parse_references_html'),
    path('upload-form/', views.upload_pdf_form, name='upload_pdf_form'),
]