from django.urls import path

from organizations import views


app_name = 'organizations'
public_api_patterns = urlpatterns = [
    path('organization/raw/<str:srn>/', views.RawOrganizationDetailView.as_view(), name="raw-organization-detail"),
    path('organization/raw/', views.RawOrganizationListView.as_view(), name="raw-organizations"),
    path(
        'organization/metadata/<str:srn>/', views.MetadataOrganizationDetailView.as_view(),
        name="metadata-organization-detail"
    ),
    path('organization/metadata/', views.MetadataOrganizationListView.as_view(), name="metadata-organizations"),
    path('organization/<str:srn>/', views.OrganizationDetailView.as_view(), name="organization-detail"),
    path('organization/', views.OrganizationListView.as_view(), name="list-organizations"),
]
