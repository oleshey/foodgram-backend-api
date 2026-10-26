import base64
import binascii

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для принятия изображений в формате Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, imgstr = data.split(';base64,', 1)
            except ValueError as exc:
                raise ValidationError(
                    'Некорректный формат изображения.'
                ) from exc

            mime = header.split(':', 1)[1] if ':' in header else ''
            ext = mime.split('/', 1)[1] if '/' in mime else 'png'

            try:
                decoded = base64.b64decode(imgstr, validate=True)
            except (TypeError, ValueError, binascii.Error) as exc:
                raise ValidationError(
                    'Некорректные Base64-данные изображения.'
                ) from exc

            return ContentFile(decoded, name=f'upload.{ext}')

        return super().to_internal_value(data)
