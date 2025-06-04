import os

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):

    def save(self, name, content, max_length=None):
        """
        Override save to skip validation in DEBUG mode
        """
        if settings.DEBUG:  # skips SuspiciousFileOperation checks on localhost
            if content is None:
                return name

            if not hasattr(content, 'chunks'):
                content = File(content, name)

            # Get the name without validation
            name = self.get_available_name(name, max_length=max_length)
            name = self._save(name, content)
            return name
        else:  # use default behavior in production
            return super().save(name, content, max_length)

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
