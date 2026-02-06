from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)

        user_type = 'admin' if user.is_staff and user.is_superuser else 'student'
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
           ' user_type': user_type,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data

        if request.user.is_staff or request.user.is_superuser:
         data[' user_type'] = 'admin'

        else:
            data[' user_type'] = 'student'

            if hasattr(request.user, 'student_profile'):
                data['has_student_profile'] = True
            else:
                data['has_student_profile'] = False
                
        return Response(data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        

class IsAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = request.user.is_staff and request.user.is_superuser
        return Response({'is_admin': is_admin,
                         'user_type': 'admin' if is_admin else 'student'
                         })