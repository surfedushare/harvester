from django.urls import path

from products import views


app_name = 'products'
public_api_patterns = urlpatterns = [
    path('product/raw/<str:srn>/', views.RawProductDetailView.as_view(), name="raw-product-detail"),
    path('product/raw/', views.RawProductListView.as_view(), name="raw-products"),
    path(
        'product/metadata/<str:srn>/', views.MetadataProductDetailView.as_view(),
        name="metadata-product-detail"
    ),
    path('product/metadata/', views.MetadataProductListView.as_view(), name="metadata-products"),
    path('product/overwrite/', views.ProductOverwriteListView.as_view(), name="product-overwrite-list"),
    path('product/overwrite/<str:srn>/', views.ProductOverwriteDetailView.as_view(), name="product-overwrite-detail"),
    path('product/<str:srn>/', views.SearchProductDetailView.as_view(), name="product-detail"),
    path('product/', views.SearchProductListView.as_view(), name="list-products"),
]

webhook_urlpatterns = [
    path(
        'webhook/product/<str:source>:<str:set_specification>/<uuid:secret>/',
        views.product_webhook, name="product-webhook"
    )
]
