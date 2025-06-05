from apps.system.models import SystemConfig, Menu, Slider, CoreConfig


def get_system_config() -> SystemConfig:
    return SystemConfig.objects.first()


def get_core_config() -> CoreConfig:
    config = CoreConfig.objects.first()
    if config is None:
        config = CoreConfig.objects.create()
    return config


def get_menu_config():
    return Menu.objects.all()


def get_sliders():
    return Slider.objects.all()


def preprocessing_filter_spec(endpoints):
    filtered = []
    print(endpoints[0])
    for (path, path_regex, method, callback) in endpoints:
        # Remove all but DRF API endpoints
        if not path.endswith("{format}"):
            filtered.append((path, path_regex, method, callback))
    return filtered
