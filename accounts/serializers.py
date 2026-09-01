from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from common.validators import clean_text, validate_phone_number, validate_upload
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        max_length=128,
        validators=[password_validation.validate_password],
    )
    full_name = serializers.CharField(source='display_name', read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30,
        validators=[validate_phone_number],
    )
    profile_image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_upload],
    )

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'email',
            'phone_number',
            'position',
            'office',
            'profile_image',
            'role',
            'is_active',
            'is_verified',
            'last_login',
            'created_at',
            'updated_at',
            'password',
        ]
        read_only_fields = [
            'id',
            'role',
            'is_active',
            'is_verified',
            'last_login',
            'created_at',
            'updated_at',
        ]

    def validate_email(self, value):
        normalized = value.strip().lower()
        users = User.objects.filter(email__iexact=normalized)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return normalized

    def validate(self, data):
        if self.instance is None and not data.get('password'):
            raise serializers.ValidationError({'password': 'This field is required.'})
        for field, label in (
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
            ('middle_name', 'Middle name'),
            ('position', 'Position'),
            ('office', 'Office'),
        ):
            if field in data:
                data[field] = clean_text(
                    data[field],
                    field_name=label,
                    allow_blank=field not in {'first_name', 'last_name'},
                )
        if 'phone_number' in data:
            data['phone_number'] = data['phone_number'].strip()
        return data

    def create(self, data):
        password = data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'This field is required.'})
        return User.objects.create_user(password=password, **data)

    def update(self, obj, data):
        password = data.pop('password', None)
        obj = super().update(obj, data)
        if password:
            obj.set_password(password)
            obj.save(update_fields=['password', 'updated_at'])
        return obj


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='display_name', read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30,
        validators=[validate_phone_number],
    )
    profile_image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_upload],
    )

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'email',
            'phone_number',
            'position',
            'office',
            'profile_image',
            'role',
            'is_active',
            'is_verified',
            'last_login',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'role',
            'is_active',
            'is_verified',
            'last_login',
            'created_at',
            'updated_at',
        ]

    def validate_email(self, value):
        normalized = value.strip().lower()
        users = User.objects.filter(email__iexact=normalized).exclude(
            pk=self.instance.pk
        )
        if users.exists():
            raise serializers.ValidationError(
                'An account with this email already exists.'
            )
        return normalized

    def validate(self, data):
        protected = {'password', 'role', 'is_active', 'is_verified'} & set(
            self.initial_data
        )
        if protected:
            raise serializers.ValidationError(
                {
                    field: 'Use the dedicated account or password endpoint.'
                    for field in sorted(protected)
                }
            )
        for field, label in (
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
            ('middle_name', 'Middle name'),
            ('position', 'Position'),
            ('office', 'Office'),
        ):
            if field in data:
                data[field] = clean_text(
                    data[field],
                    field_name=label,
                    allow_blank=field not in {'first_name', 'last_name'},
                )
        if 'phone_number' in data:
            data['phone_number'] = data['phone_number'].strip()
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False)

    def validate(self, data):
        user = authenticate(email=data['email'].lower(), password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account is inactive.')
        if not user.is_verified:
            raise serializers.ValidationError('Account is not verified.')
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, trim_whitespace=False)
    new_password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        validators=[password_validation.validate_password],
    )


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        validators=[password_validation.validate_password],
    )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class EmptySerializer(serializers.Serializer):
    pass
