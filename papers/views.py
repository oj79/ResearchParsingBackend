# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Paper
from django.http import HttpResponse
import json

@login_required
def my_papers(request):
    user_papers = Paper.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'papers/paper_list.html', {'papers': user_papers})


@login_required
def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id, owner=request.user)
    refs = []
    if paper.references_json:
        try:
            refs = json.loads(paper.references_json)
        except:
            refs = []
    return render(request, 'papers/paper_detail.html', {
        'paper': paper,
        'references': refs
    })


@login_required
def paper_download(request, paper_id):
    """
    Securely serves the PDF from GCS by reading it and returning as HttpResponse.
    Ensures only the owner can access.
    """
    # 1. Retrieve the paper and confirm ownership
    paper = get_object_or_404(Paper, id=paper_id, owner=request.user)

    # 2. Open the file from GCS (this uses the default credentials on Cloud Run)
    paper.pdf_file.open('rb')  # "paper_obj.pdf_file" is a FileField (GCS backend)
    file_data = paper.pdf_file.read()
    paper.pdf_file.close()

    # 3. Return as a downloadable response
    #    You can detect the file mimetype if needed; here we assume PDF for example
    response = HttpResponse(file_data, content_type='application/pdf')
    # 'attachment' triggers a download; if you want inline view in browser, use 'inline'
    response['Content-Disposition'] = f'attachment; filename={paper.pdf_file.name}"'
    return response
