from django.urls import path


from testing import views


app_name = 'testing'
urlpatterns = [
    path('mocks/entity/<str:entity>/<str:since>/ids/', views.EntityMockIdListAPIView.as_view(), name="entity-ids"),
    path('mocks/entity/<str:entity>/<str:pk>/', views.EntityMockDetailAPIView.as_view(), name="entity-details"),
    path('mocks/entity/<str:entity>/<str:since>', views.EntityMockAPIView.as_view(), name="entities"),
]
