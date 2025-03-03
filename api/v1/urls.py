from django.urls import path, include
from rest_framework.routers import DefaultRouter
from depot.views import (
    DepotViewSet, MessageViewSet, 
    ScheduleViewSet, AnnouncementViewSet,OfficerViewSet
)

router = DefaultRouter()
router.register(r'depots', DepotViewSet)
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
router.register(r'announcements', AnnouncementViewSet)
router.register(r'officers', OfficerViewSet, basename='officer')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]