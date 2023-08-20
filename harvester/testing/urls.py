from django.urls import path


from testing import views


app_name = 'testing'
urlpatterns = [
    path('mocks/entity/merge/', views.EntityMockIdListAPIView.as_view(), kwargs={"entity": "simple"}),
    path('mocks/entity/merge/<str:pk>/', views.EntityMockDetailAPIView.as_view(), kwargs={"entity": "simple"}),
    path('mocks/entity/<str:entity>/', views.EntityMockAPIView.as_view()),
]
