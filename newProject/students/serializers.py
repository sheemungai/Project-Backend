from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    userName = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    firstName = serializers.CharField(source='user.first_name', read_only=True)
    lastName = serializers.CharField(source='user.last_name', read_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name', 
                  'address', 'dob', 'gender', 'phone', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'user', 'createdAt', 'updatedAt']