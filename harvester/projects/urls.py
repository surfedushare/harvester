from django.urls import path

from projects import views


app_name = 'projects'
public_api_patterns = urlpatterns = [
    path('project/raw/<str:srn>/', views.RawProjectDetailView.as_view(), name="raw-project-detail"),
    path('project/raw/', views.RawProjectListView.as_view(), name="raw-projects"),
    path(
        'project/metadata/<str:srn>/', views.MetadataProjectDetailView.as_view(),
        name="metadata-project-detail"
    ),
    path('project/metadata/', views.MetadataProjectListView.as_view(), name="metadata-projects"),
    path('project/<str:srn>/', views.SearchProjectDetailView.as_view(), name="project-detail"),
    path('project/', views.SearchProjectListView.as_view(), name="list-projects"),
]
