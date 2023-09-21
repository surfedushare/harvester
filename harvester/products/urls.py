from django.urls import path

from products import views


app_name = 'products'
public_api_patterns = [
    path('product/raw/<str:srn>/', views.RawProductDetailView.as_view(), name="raw-product-detail"),
    path('product/raw/', views.RawProductListView.as_view(), name="raw-products"),
    path(
        'product/metadata/<str:srn>/', views.MetadataProductDetailView.as_view(),
        name="metadata-product-detail"
    ),
    path('product/metadata/', views.MetadataProductListView.as_view(), name="metadata-products"),
    path('product/<str:srn>/', views.SearchProductDetailView.as_view(), name="product-detail"),
    path('product/', views.SearchProductListView.as_view(), name="list-products"),
]
urlpatterns = public_api_patterns
