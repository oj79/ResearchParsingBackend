from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import tempfile
from .advanced_references_extraction import grobid_extract_references

@csrf_exempt
def parse_references_html(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return render(request, 'parsing/references_table.html', {"references": []})

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        references_list = []
        try:
            references_list = grobid_extract_references(tmp_path)
        except Exception as e:
            print(f"Error extracting references: {e}")

        return render(request, 'parsing/references_table.html', {"references": references_list})

    else:
        # GET request -> show the upload form
        return render(request, 'parsing/upload_pdf_form.html')



def upload_pdf_form(request):
    """
    Displays a simple HTML form to choose a PDF file and submit it
    to the `parse_references_html` endpoint.
    """
    return render(request, 'parsing/upload_pdf_form.html')