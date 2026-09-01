import math

from django.db.models import Q
from rest_framework.exceptions import ValidationError


MAX_NEARBY_RADIUS_KM = 500.0


def distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    latitude_delta = math.radians(float(lat2) - float(lat1))
    longitude_delta = math.radians(float(lon2) - float(lon1))
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(longitude_delta / 2) ** 2
    )
    # Floating point rounding can otherwise put this just outside [0, 1].
    haversine = min(1.0, max(0.0, haversine))
    return 6371.0088 * 2 * math.atan2(
        math.sqrt(haversine), math.sqrt(1 - haversine)
    )


def nearby_parameters(request, *, default_radius):
    errors = {}
    values = {}
    for name in ("latitude", "longitude", "radius"):
        raw = request.query_params.get(
            name,
            str(default_radius) if name == "radius" else None,
        )
        try:
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError
            values[name] = value
        except (TypeError, ValueError):
            errors[name] = [f"{name.title()} must be a valid number."]

    latitude = values.get("latitude")
    longitude = values.get("longitude")
    radius = values.get("radius")
    if latitude is not None and not -90 <= latitude <= 90:
        errors["latitude"] = ["Latitude must be between -90 and 90."]
    if longitude is not None and not -180 <= longitude <= 180:
        errors["longitude"] = ["Longitude must be between -180 and 180."]
    if radius is not None and not 0 < radius <= MAX_NEARBY_RADIUS_KM:
        errors["radius"] = [
            f"Radius must be greater than zero and no more than {MAX_NEARBY_RADIUS_KM:g} km."
        ]
    if errors:
        raise ValidationError(errors)
    return latitude, longitude, radius


def within_bounding_box(queryset, latitude, longitude, radius):
    """Use indexed coordinates to reduce rows before exact Haversine checks."""
    latitude_delta = radius / 110.574
    minimum_latitude = max(-90.0, latitude - latitude_delta)
    maximum_latitude = min(90.0, latitude + latitude_delta)
    queryset = queryset.filter(latitude__range=(minimum_latitude, maximum_latitude))

    cosine = abs(math.cos(math.radians(latitude)))
    if cosine < 1e-9:
        return queryset
    longitude_delta = min(180.0, radius / (111.320 * cosine))
    minimum_longitude = longitude - longitude_delta
    maximum_longitude = longitude + longitude_delta
    if minimum_longitude < -180:
        return queryset.filter(
            Q(longitude__gte=minimum_longitude + 360)
            | Q(longitude__lte=maximum_longitude)
        )
    if maximum_longitude > 180:
        return queryset.filter(
            Q(longitude__gte=minimum_longitude)
            | Q(longitude__lte=maximum_longitude - 360)
        )
    return queryset.filter(longitude__range=(minimum_longitude, maximum_longitude))
