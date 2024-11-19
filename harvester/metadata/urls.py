from django.urls import path

from metadata import views


app_name = 'metadata'
public_api_patterns = urlpatterns = [
    path('metadata/tree/', views.MetadataTreeView.as_view()),
    path('metadata/field-values/<str:field>/', views.MetadataFieldValuesView.as_view()),
    path('metadata/field-values/<str:field>/<str:startswith>/', views.MetadataFieldValuesView.as_view()),
]
html_patterns = [
    path('metadata/tree/plain/', views.MetadataTreeHTMLView.as_view()),
]
