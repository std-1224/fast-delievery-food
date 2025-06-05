from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from apps.system import choices
from settings import FIREBASE_KEY_FILE_STORAGE


class SystemConfig(models.Model):
    currency = models.CharField(_("Currency"), max_length=25)
    logo = models.ImageField(
        _("Logo"), upload_to="image", blank=True, null=True, max_length=255
    )
    site_name = models.CharField(_("Site name"), max_length=100, default="KM")
    favicon = models.ImageField(
        _("Favicon"), upload_to="image", blank=True, null=True, max_length=255
    )
    phone = models.CharField(max_length=20, default="")
    email = models.EmailField(max_length=255, default="example@example.com")
    header_background = models.CharField(max_length=255, default="white")
    header_fontsize = models.IntegerField(default=20, help_text="in px")
    header_fontcolor = models.CharField(max_length=255, default="white")
    home_page_layout = models.CharField(
        max_length=100,
        choices=choices.HOME_PAGE_LAYOUT_CHOICES,
        default=choices.SLIDER_LAYOUT,
    )
    home_page_background_image = models.ImageField(
        _("Home page background image"),
        upload_to="image",
        blank=True,
        null=True,
        max_length=255,
    )
    footer_background = models.CharField(max_length=255, default="white")
    footer_padding_top = models.IntegerField(default=20, help_text="in px")
    footer_padding_side = models.IntegerField(default=20, help_text="in percent")
    footer_padding_bottom = models.IntegerField(default=20, help_text="in px")
    footer_column_1 = HTMLField(default="", blank=True)
    footer_column_2 = HTMLField(default="", blank=True)
    footer_column_3 = HTMLField(default="", blank=True)
    footer_column_4 = HTMLField(default="", blank=True)
    footer_end_line = HTMLField(default="", blank=True)
    display_product = models.BooleanField(default=True)

    # business information
    business_logo = models.ImageField(
        _("business Logo"), upload_to="image", blank=True, null=True, max_length=255
    )
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_address = models.CharField(max_length=255, blank=True, null=True)
    business_header_cuisines = models.CharField(max_length=255, blank=True, null=True)
    default_cooking_time = models.IntegerField(default=15, help_text="In minutes")
    default_delivery_time = models.IntegerField(default=10, help_text="In minutes")
    collection_pre_order_days = models.IntegerField(default=0,
                                                    help_text="How far in future customer can get his order. Set to zero if customer can order only for same day.")
    delivery_pre_order_days = models.IntegerField(default=3,
                                                  help_text="How far in future customer can get his order. Set to zero if customer can order only for same day.")


class CoreConfig(models.Model):
    stripe_publish_key = models.CharField(max_length=255, blank=True, null=True)
    stripe_secret_key = models.CharField(max_length=255, blank=True, null=True)
    paypal_client_id = models.CharField(max_length=255, blank=True, null=True)
    paypal_secret_key = models.CharField(max_length=255, blank=True, null=True)
    notification_admin_emails = models.CharField(max_length=255, blank=True, null=True,
                                                 help_text="Comma separated emails")
    firebase_service_account = models.FileField(storage=FIREBASE_KEY_FILE_STORAGE, null=True,
                                                help_text="Firebase service key file use for push notification")


class Menu(models.Model):
    label = models.CharField(_("Label"), max_length=255)
    url = models.URLField(_("URL"))
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        ordering = ["order"]


class Slider(models.Model):
    title = models.CharField(max_length=100, default="")
    name = models.CharField(max_length=100, default="")
    content = models.CharField(max_length=100, default="")
    button_label = models.CharField(max_length=50)
    image = models.ImageField(
        _("Image"), upload_to="image", blank=True, null=True, max_length=255
    )


class ScheduleConfig(models.Model):
    DAY_CHOICES = (
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    )

    day = models.CharField(max_length=255, choices=DAY_CHOICES)
    open_time = models.TimeField(null=False, blank=False)
    close_time = models.TimeField(null=False, blank=False)
    delivery_open_time = models.TimeField(null=False, blank=False)
    delivery_close_time = models.TimeField(null=False, blank=False)
    collection_open_time = models.TimeField(null=False, blank=False)
    collection_close_time = models.TimeField(null=False, blank=False)
    ordering_open_time = models.TimeField(null=False, blank=False)
    ordering_close_time = models.TimeField(null=False, blank=False)

    class Meta:
        ordering = ["day"]
        verbose_name = _("Schedule Configuration")
        verbose_name_plural = _("Schedule Configurations")

    def init_default_schedule(self):
        for day in self.DAY_CHOICES:
            ScheduleConfig.objects.create(day=day[0])


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, null=True, blank=False)
    public_key = models.CharField(max_length=255, null=True, blank=False)
    app_id = models.CharField(max_length=255, null=True, blank=False)
    firebase_token = models.CharField(max_length=255, null=True, blank=True)
    is_connected = models.BooleanField(default=False)
