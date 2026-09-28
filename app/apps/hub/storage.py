import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """Хранилище приватных файлов (договоры, документы).

    Лежит вне MEDIA_ROOT и не имеет base_url: у файла нет публичной ссылки,
    отдавать его можно только через view с проверкой прав доступа.
    """

    def __init__(self, **kwargs):
        kwargs['base_url'] = None
        super().__init__(**kwargs)

    # Путь читается из настроек при каждом обращении (а не один раз при импорте),
    # чтобы работали override_settings в тестах и смена PRIVATE_MEDIA_ROOT
    @property
    def base_location(self):
        return self._location or settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise NotImplementedError(
            'Приватные файлы не имеют публичного URL — отдавайте их через защищённый view.'
        )


def private_storage():
    """Callable для FileField(storage=private_storage) — сериализуется в миграциях."""
    return PrivateMediaStorage()
