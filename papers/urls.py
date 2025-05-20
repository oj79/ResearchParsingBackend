from django.urls import path
from . import views
from .views import my_papers, paper_detail, paper_download

app_name = 'papers'

urlpatterns = [
    path('my-papers/', views.my_papers, name='my_papers'),
    path('detail/<int:paper_id>/', views.paper_detail, name='paper_detail'),
    path('download/<int:paper_id>/', paper_download, name='paper_download'),
]
