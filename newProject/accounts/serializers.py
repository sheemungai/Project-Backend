from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(
        choices =('student','admin'),
        required= False,
        default ='student'
    )


    class Meta:
        model = User
        fields = ('first_name','last_name','username', 'email',  'password', 'password2', 'user_type')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user_type = validated_data.pop('user_type', 'student')

        user = User.objects.create_user(**validated_data)
        if user_type == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type')

    def get_user_type(self, obj):
        if obj.is_staff and obj.is_superuser:
            return 'admin'
        return 'student'