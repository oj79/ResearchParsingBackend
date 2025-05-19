from django.urls import path
from . import views

app_name = 'parsing'

urlpatterns = [
    # Add a URL pattern for your HTML-based parsing view:
    path('parse-references-html/', views.parse_references_html, name='parse_references_html'),
    path('parse-methods-html/', views.parse_methods_html, name='parse_methods_html'),
    path('upload-form/', views.upload_pdf_form, name='upload_pdf_form'),
    path('parse-methods-and-tables/', views.parse_methods_and_tables_html, name='parse_methods_and_tables_html'),
    path('parse-methods-and-tables-summary/', views.parse_methods_and_tables_summarize,
         name='parse_methods_and_tables_summarize'),
]