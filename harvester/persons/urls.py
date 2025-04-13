from django.urls import path

from persons import views


app_name = 'persons'
public_api_patterns = urlpatterns = [
    path('person/raw/<str:srn>/', views.RawPersonDetailView.as_view(), name="raw-person-detail"),
    path('person/raw/', views.RawPersonListView.as_view(), name="raw-persons"),
    path(
        'person/metadata/<str:srn>/', views.MetadataPersonDetailView.as_view(),
        name="metadata-person-detail"
    ),
    path('person/metadata/', views.MetadataPersonListView.as_view(), name="metadata-persons"),
    path('person/<str:srn>/', views.PersonDetailView.as_view(), name="person-detail"),
    path('person/', views.PersonListView.as_view(), name="list-persons"),
]
