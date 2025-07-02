Research Parsing Backend
=======================

This Django project provides a small web service for parsing research papers in PDF form. Uploaded files are processed with [GROBID](https://grobid.readthedocs.io) and tabula to extract references, methods text and tables. The data can optionally be summarized with OpenAI models. The application supports Google OAuth login and uses Google Cloud Storage for storing PDFs.

## Features

- **PDF Parsing Endpoints** – The `parsing` app exposes several routes for processing PDFs. For example, `parse-references-html` parses a PDF with GROBID and returns a references table, while `parse-methods-and-tables-summary` runs methods and table extraction then summarizes the content using ChatGPT. These routes are declared in `parsing/urls.py`:

```
path('parse-references-html/', views.parse_references_html, name='parse_references_html')
path('parse-methods-html/', views.parse_methods_html, name='parse_methods_html')
path('upload-form/', views.upload_pdf_form, name='upload_pdf_form')
path('parse-methods-and-tables/', views.parse_methods_and_tables_html, name='parse_methods_and_tables_html')
path('parse-methods-and-tables-summary/', views.parse_methods_and_tables_summarize, name='parse_methods_and_tables_summarize')
```

- **Paper Model** – Uploaded PDFs and their parse results are stored in the `Paper` model. It tracks the owner, hash, parse type and fields for references, methods text, tables and a summary:

```
class Paper(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='papers')
    pdf_file = models.FileField(upload_to='uploaded_pdfs/')
    pdf_hash = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    parse_type = models.CharField(max_length=50, choices=[('references_only','References Only'),('methods_tables_only','Methods & Tables Only'),('both','Both References & Methods+Tables')], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    references_json = models.TextField(blank=True)
    methods_text = models.TextField(blank=True)
    tables_json = models.TextField(blank=True)
    summary_text = models.TextField(blank=True)
```

- **Cloud Storage Integration** – Files are stored in Google Cloud Storage by default. The storage backend is configured in `settings.py`:

```
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {"project_id": "research-parsing", "bucket_name": "my-research-parsing-bucket"},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
}
```

- **PDF Processing Logic** – `parsing/views.py` handles uploading a PDF, temporarily storing it, sending it to GROBID, calling the OpenAI APIs for filtering references or summarizing methods and tables, and saving results. Processing is done in functions like `parse_references_html` and `parse_methods_and_tables_summarize`.

- **OpenAI Post‑processing** – `ai_postprocess.py` defines helper functions that call the OpenAI API. References from GROBID can be validated in chunks and methods/tables results can be summarized:

```
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
...
summary = summarize_methods_and_tables_with_chatgpt(methods_text, tables_str)
```

- **Docker Support** – A Dockerfile is provided for deploying to Cloud Run. It installs Java for tabula, installs Python requirements, and runs the app using gunicorn on port 8080:

```
FROM python:3.12-slim
RUN apt-get update && apt-get install -y default-jre && apt-get clean
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--timeout=600", "ResearchParsing.wsgi"]
```

## Setup

1. **Install Dependencies** – Create a virtual environment with Python 3.12 and install packages from `requirements.txt`.
2. **Environment Variables** – Set variables such as `OPENAI_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` and the Django `SECRET_KEY`. Configure `GROBID_BASE_URL` to point at your GROBID service.
3. **Database Migrations** – Run `python manage.py migrate` to set up the SQLite database (or adjust settings for PostgreSQL).
4. **Run the Server** – Start the development server with `python manage.py runserver` or build the Docker image and run via gunicorn.

Note: If you would like to try the app, please send me your email so that I can add you to the allowed users

## Testing

Unit test files are present but contain no tests yet. Running `python manage.py test` requires dependencies such as `python-dotenv`.

## Repository Structure

- `accounts/` – adapters and views for Google login
- `papers/` – model and views for storing parsed papers
- `parsing/` – PDF parsing logic, templates and OpenAI helpers
- `templates/` – base templates for login and upload forms

This README provides a high‑level overview of the codebase and how to run it locally or in Docker.