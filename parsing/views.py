from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import tempfile
from ResearchParsing.papers.models import Paper, compute_file_hash

from .advanced_references_extraction import grobid_extract_references
from .ai_postprocess import filter_grobid_references_with_chatgpt
from .advanced_methods_extraction import grobid_extract_methods
from .table_extraction import parse_methods_and_tables, tables_to_json, parse_tables_comprehensive
from .ai_postprocess import summarize_methods_and_tables_with_chatgpt
import os
import hashlib, json

# @login_required
# def parse_references_html(request):
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')
#         if not pdf_file:
#             return render(request, 'parsing/references_table.html', {"references": []})
#
#         temp_hash = _compute_temp_file_hash(pdf_file)
#         requested_parse = 'references_only'
#         existing_paper = Paper.objects.filter(owner=request.user, pdf_hash=temp_hash).first()
#
#         if existing_paper:
#             merged = _merge_parse_types(existing_paper.parse_type, requested_parse)
#             existing_paper.parse_type = merged
#             existing_paper.save()
#             pdf_path = existing_paper.pdf_file.path
#             paper_obj = existing_paper
#         else:
#             paper_obj = Paper.objects.create(
#                 owner=request.user,
#                 pdf_file=pdf_file,
#                 pdf_hash=temp_hash,
#                 parse_type=requested_parse
#             )
#             pdf_path = paper_obj.pdf_file.path
#
#         refs = []
#         try:
#             refs = grobid_extract_references(pdf_path)
#             refs = filter_grobid_references_with_chatgpt(refs)
#         except Exception as e:
#             print("Error extracting references:", e)
#
#         # Store references for detail view
#         paper_obj.references_json = json.dumps(refs)
#         paper_obj.save()
#
#         return render(request, 'parsing/references_table.html', {"references": refs})
#     return render(request, 'parsing/upload_pdf_form.html')

@login_required
def parse_references_html(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/references_table.html', {"references": []})

        # Create or find existing Paper object as before (no change)
        temp_hash = _compute_temp_file_hash(pdf_file)
        requested_parse = 'references_only'
        existing_paper = Paper.objects.filter(owner=request.user, pdf_hash=temp_hash).first()

        if existing_paper:
            merged = _merge_parse_types(existing_paper.parse_type, requested_parse)
            existing_paper.parse_type = merged
            existing_paper.save()
            paper_obj = existing_paper
        else:
            paper_obj = Paper.objects.create(
                owner=request.user,
                pdf_file=pdf_file,
                pdf_hash=temp_hash,
                parse_type=requested_parse
            )

        #print("DEBUG => paper_obj.pdf_file.storage:", paper_obj.pdf_file.storage)
        #print("DEBUG => storage class:", type(paper_obj.pdf_file.storage))

        # Instead of using pdf_file.path, open the file from storage, copy to a NamedTemporaryFile
        references_list = []
        try:
            # 1) Open the file from GCS (or local if you're still in dev)
            paper_obj.pdf_file.open('rb')  # ensure file-like object is ready
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                for chunk in paper_obj.pdf_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            paper_obj.pdf_file.close()

            # 2) Pass tmp_path to grobid_extract_references
            references_list = grobid_extract_references(tmp_path)
            references_list = filter_grobid_references_with_chatgpt(references_list)

        except Exception as e:
            print("Error extracting references:", e)

        # 3) Store references in the Paper record
        paper_obj.references_json = json.dumps(references_list)
        paper_obj.save()

        return render(request, 'parsing/references_table.html', {"references": references_list})

    return render(request, 'parsing/upload_pdf_form.html')


@login_required
def upload_pdf_form(request):
    """
    Displays a simple HTML form to choose a PDF file and submit it
    to the `parse_references_html` endpoint.
    """
    return render(request, 'parsing/upload_pdf_form.html')


@csrf_exempt
def parse_methods_html(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/methods_text.html', {"methods_text": ""})

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        try:
            # Basic extraction of methods text (including GROBID's formula text)
            methods_text = grobid_extract_methods(tmp_path)
        except Exception as e:
            print(f"Error extracting methods: {e}")
            methods_text = ""

        return render(request, 'parsing/methods_text.html', {"methods_text": methods_text})
    else:
        return render(request, 'parsing/upload_pdf_form.html')


@csrf_exempt
def parse_tables_html(request):
    """
    Demo view that lets a user upload a PDF, tries all advanced Tabula passes,
    and returns the JSON in an HTML page.
    """
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/tables_view.html', {"tables_json": "No file uploaded."})

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        df_list = parse_tables_comprehensive(tmp_path, pages="all")
        # Convert to JSON for demonstration
        tables_json = tables_to_json(df_list)

        return render(request, 'parsing/tables_view.html', {"tables_json": tables_json})
    else:
        return render(request, 'parsing/upload_pdf_form.html')


@csrf_exempt
def parse_methods_and_tables_html(request):
    """
    Single endpoint + single button approach:
    - Extract methods text
    - Extract tables
    - Display both
    """
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/methods_and_tables.html', {
                "methods_text": "",
                "tables_json": "No file uploaded."
            })

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        methods_text = ""
        df_list = []

        try:
            methods_text, df_list = parse_methods_and_tables(tmp_path, pages="all")
        except Exception as e:
            print(f"Error parsing methods/tables: {e}")

        # Convert DataFrames to JSON for easy viewing
        tables_json = tables_to_json(df_list)

        return render(request, 'parsing/methods_and_tables.html', {
            "methods_text": methods_text,
            "tables_json": tables_json
        })
    else:
        return render(request, 'parsing/upload_pdf_form.html')


# @login_required
# def parse_methods_and_tables_summarize(request):
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')
#         if not pdf_file:
#             return render(request, 'parsing/methods_tables_summary.html', {
#                 "summary_text": "No file uploaded."
#             })
#
#         temp_hash = _compute_temp_file_hash(pdf_file)
#         requested_parse = 'methods_tables_only'
#         existing_paper = Paper.objects.filter(owner=request.user, pdf_hash=temp_hash).first()
#
#         if existing_paper:
#             merged = _merge_parse_types(existing_paper.parse_type, requested_parse)
#             existing_paper.parse_type = merged
#             existing_paper.save()
#             pdf_path = existing_paper.pdf_file.path
#             paper_obj = existing_paper
#         else:
#             paper_obj = Paper.objects.create(
#                 owner=request.user,
#                 pdf_file=pdf_file,
#                 pdf_hash=temp_hash,
#                 parse_type=requested_parse
#             )
#             pdf_path = paper_obj.pdf_file.path
#
#         methods_txt, df_list = "", []
#         try:
#             methods_txt, df_list = parse_methods_and_tables(pdf_path, pages="all")
#         except Exception as e:
#             print("Error parsing PDF for methods & tables:", e)
#
#         tables_str = tables_to_json(df_list)
#         summary = summarize_methods_and_tables_with_chatgpt(methods_txt, tables_str)
#
#         # Store results for detail view
#         paper_obj.methods_text = methods_txt
#         paper_obj.tables_json = tables_str
#         paper_obj.summary_text = summary
#         paper_obj.save()
#
#         return render(request, 'parsing/methods_tables_summary.html', {
#             "summary_text": summary
#         })
#     return render(request, 'parsing/upload_pdf_form.html')


@login_required
def parse_methods_and_tables_summarize(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/methods_tables_summary.html', {
                "summary_text": "No file uploaded."
            })

        temp_hash = _compute_temp_file_hash(pdf_file)
        requested_parse = 'methods_tables_only'
        existing_paper = Paper.objects.filter(owner=request.user, pdf_hash=temp_hash).first()

        if existing_paper:
            merged = _merge_parse_types(existing_paper.parse_type, requested_parse)
            existing_paper.parse_type = merged
            existing_paper.save()
            paper_obj = existing_paper
        else:
            paper_obj = Paper.objects.create(
                owner=request.user,
                pdf_file=pdf_file,
                pdf_hash=temp_hash,
                parse_type=requested_parse
            )

        # === DEBUG PRINT: Check storage backend being used ===
        #print("DEBUG => paper_obj.pdf_file.storage:", paper_obj.pdf_file.storage)
        #print("DEBUG => storage class:", type(paper_obj.pdf_file.storage))

        methods_text, df_list = "", []
        try:
            # 1) Open the PDF from GCS (or local if dev), copy to a NamedTemporaryFile
            paper_obj.pdf_file.open('rb')
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                for chunk in paper_obj.pdf_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            paper_obj.pdf_file.close()

            # 2) Parse methods & tables from tmp_path
            methods_text, df_list = parse_methods_and_tables(tmp_path, pages="all")

            # 3) Summarize with the LLM
            tables_str = tables_to_json(df_list)
            summary = summarize_methods_and_tables_with_chatgpt(methods_text, tables_str)

            # 4) Save the results in the Paper record
            paper_obj.methods_text = methods_text
            paper_obj.tables_json = tables_str
            paper_obj.summary_text = summary
            paper_obj.save()

        except Exception as e:
            print("Error parsing PDF for methods & tables:", e)

        return render(request, 'parsing/methods_tables_summary.html', {
            "summary_text": paper_obj.summary_text
        })

    # For GET or no file
    return render(request, 'parsing/upload_pdf_form.html')



def _merge_parse_types(existing_type, new_type):
    if existing_type == new_type:
        return existing_type
    pair = {existing_type, new_type}
    if pair == {'references_only', 'methods_tables_only'}:
        return 'both'
    if 'both' in pair:
        return 'both'
    return new_type


def _compute_temp_file_hash(uploaded_file):
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()
