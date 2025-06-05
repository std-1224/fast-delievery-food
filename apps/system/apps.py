from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig


class SystemConfigAppConfig(OscarDashboardConfig):
    name = 'apps.system'
    label = "system"
    namespace = "system"
    verbose_name = _("System")

    default_permissions = ["is_staff"]
    permissions_map = {
        'link-device': (['is_staff'], ['partner.dashboard_access']),
    }

    def get_urls(self):
        from .views import ScheduleConfigView, LinkDeviceView

        urlpatterns = [
            path('schedule/', ScheduleConfigView.as_view(), name='schedule-config'),
            path('link-device/', LinkDeviceView.as_view(), name='link-device'),
        ]
        return self.post_process_urls(urlpatterns)
