# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Paper
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
