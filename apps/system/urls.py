from django.urls import path

from .views import ScheduleConfigView, LinkDeviceView

urlpatterns = [
    path('schedule/', ScheduleConfigView.as_view(), name='schedule-config'),
    path('link-device/', LinkDeviceView.as_view(), name='link-device'),
]
