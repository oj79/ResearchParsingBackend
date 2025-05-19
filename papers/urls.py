from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    path('my-papers/', views.my_papers, name='my_papers'),
    path('detail/<int:paper_id>/', views.paper_detail, name='paper_detail'),
]
