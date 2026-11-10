from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/apply/', views.apply_to_project, name='apply_to_project'),
    path('applications/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('applications/<int:application_id>/reject/', views.reject_application, name='reject_application'),
]
