from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """Хранилище приватных файлов (договоры, документы).

    Лежит вне MEDIA_ROOT и не имеет base_url: у файла нет публичной ссылки,
    отдавать его можно только через view с проверкой прав доступа.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('location', settings.PRIVATE_MEDIA_ROOT)
        kwargs['base_url'] = None
        super().__init__(**kwargs)

    def url(self, name):
        raise NotImplementedError(
            'Приватные файлы не имеют публичного URL — отдавайте их через защищённый view.'
        )


def private_storage():
    """Callable для FileField(storage=private_storage) — сериализуется в миграциях."""
    return PrivateMediaStorage()
