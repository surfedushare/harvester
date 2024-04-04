from django.urls import path
from rest_framework import routers

from core import views


router = routers.SimpleRouter()
router.register("query", views.QueryViewSet)


app_name = 'core'
deprecated_api_patterns = []
public_api_patterns = [
    # Documents
    path('document/raw/<str:external_id>/', views.RawDocumentDetailView.as_view(), name="raw-document-detail"),
    path('document/raw/', views.RawDocumentListView.as_view(), name="raw-documents"),
    path('document/<str:external_id>/', views.SearchDocumentDetailView.as_view(), name="document-detail"),
    path('document/', views.SearchDocumentListView.as_view(), name="list-documents"),
]
urlpatterns = public_api_patterns + router.urls + deprecated_api_patterns
