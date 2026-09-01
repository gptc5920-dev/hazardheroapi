import os
import re
import xml.etree.ElementTree as ElementTree
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from PIL import Image


ALLOWED = {'.jpg', '.jpeg', '.png', '.webp', '.pdf', '.doc', '.docx'}
IMAGE = {'.jpg', '.jpeg', '.png', '.webp'}
VECTOR = {'.svg'}
VIDEO = {'.mp4', '.webm', '.mov'}
MEDIA = IMAGE | VECTOR | VIDEO
SUBTITLES = {'.vtt', '.srt'}
PHONE_CHARACTERS = re.compile(r'^\+?[0-9()\-\s.]+$')
CONTROL_CHARACTERS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def clean_text(value, *, field_name='Value', allow_blank=False):
    normalized = str(value or '').strip()
    if not normalized and not allow_blank:
        raise ValidationError(f'{field_name} cannot be blank.')
    if CONTROL_CHARACTERS.search(normalized):
        raise ValidationError(f'{field_name} contains unsupported characters.')
    return normalized


def validate_phone_number(value):
    if value in (None, ''):
        return
    normalized = str(value).strip()
    if not PHONE_CHARACTERS.fullmatch(normalized):
        raise ValidationError('Enter a valid phone number.')
    digit_count = sum(character.isdigit() for character in normalized)
    if not 3 <= digit_count <= 15:
        raise ValidationError('Phone numbers must contain between 3 and 15 digits.')


def validate_latitude(value):
    _validate_coordinate(value, minimum=-90, maximum=90, label='Latitude')


def validate_longitude(value):
    _validate_coordinate(value, minimum=-180, maximum=180, label='Longitude')


def _validate_coordinate(value, *, minimum, maximum, label):
    try:
        coordinate = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f'{label} must be a valid number.')
    if not minimum <= coordinate <= maximum:
        raise ValidationError(f'{label} must be between {minimum} and {maximum}.')


def clean_string_list(value, *, field_name='Items', max_items=100, max_length=180):
    if not isinstance(value, list):
        raise ValidationError(f'{field_name} must be a list.')
    if len(value) > max_items:
        raise ValidationError(
            f'{field_name} cannot contain more than {max_items} entries.'
        )
    cleaned = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            raise ValidationError(f'{field_name} must contain only text values.')
        normalized = clean_text(item, field_name=field_name.rstrip('s'))
        if len(normalized) > max_length:
            raise ValidationError(
                f'{field_name.rstrip("s")} entries must be {max_length} characters or fewer.'
            )
        if normalized not in seen:
            cleaned.append(normalized)
            seen.add(normalized)
    return cleaned


def validate_upload(upload):
    extension = os.path.splitext(upload.name)[1].lower()
    if extension not in ALLOWED:
        raise ValidationError('Unsupported file type.')
    if not upload.size:
        raise ValidationError('Empty files are not allowed.')
    if upload.size > 10 * 1024 * 1024:
        raise ValidationError('File exceeds 10 MB.')
    if extension in IMAGE:
        try:
            image = Image.open(upload)
            image.verify()
            upload.seek(0)
            if image.width > 8000 or image.height > 8000:
                raise ValidationError('Image dimensions exceed 8000x8000.')
        except ValidationError:
            raise
        except Exception as error:
            raise ValidationError('Corrupted image.') from error


def validate_media_upload(upload):
    extension = os.path.splitext(upload.name)[1].lower()
    if extension not in MEDIA:
        raise ValidationError(
            'Only JPEG, PNG, WebP, SVG, MP4, WebM, and MOV media are allowed.'
        )
    if not upload.size or upload.size > 100 * 1024 * 1024:
        raise ValidationError('Media must be non-empty and no larger than 100 MB.')
    if extension in IMAGE:
        validate_upload(upload)
    elif extension in VECTOR:
        validate_svg_upload(upload)


def validate_svg_upload(upload):
    if not upload.size:
        raise ValidationError('Empty SVG files are not allowed.')
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError('SVG files must be 5 MB or smaller.')
    try:
        content = upload.read().decode('utf-8')
        upload.seek(0)
        lowered = content.lower()
        forbidden = ('<!doctype', '<!entity', '<script', 'javascript:', 'onload=')
        if any(token in lowered for token in forbidden):
            raise ValidationError('SVG contains unsafe embedded content.')
        root = ElementTree.fromstring(content)
        if root.tag.split('}')[-1].lower() != 'svg':
            raise ValidationError('The uploaded file is not a valid SVG.')
    except ValidationError:
        raise
    except (UnicodeDecodeError, ElementTree.ParseError) as error:
        raise ValidationError('The uploaded SVG is invalid or corrupted.') from error


def validate_subtitle(upload):
    if os.path.splitext(upload.name)[1].lower() not in SUBTITLES:
        raise ValidationError('Only VTT or SRT subtitles are allowed.')
    if not upload.size or upload.size > 2 * 1024 * 1024:
        raise ValidationError('Subtitle must be non-empty and no larger than 2 MB.')
