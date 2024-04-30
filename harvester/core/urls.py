from rest_framework import routers

from core import views


router = routers.SimpleRouter()
router.register("query", views.QueryViewSet)


app_name = 'core'
urlpatterns = router.urls
