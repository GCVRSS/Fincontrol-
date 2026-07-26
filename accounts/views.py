from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .serializers import RegisterSerializer, VerifyEmailSerializer
from .models import Profile


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = user.profile.verification_token

            send_mail(
                subject='Confirme seu e-mail - FinControl',
                message=f'Use este código para verificar sua conta: {token}',
                from_email='noreply@fincontrol.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {'message': 'Usuário criado com sucesso! Verifique seu e-mail.'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                profile = Profile.objects.get(verification_token=token)
            except Profile.DoesNotExist:
                return Response(
                    {'error': 'Token inválido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if profile.is_verified:
                return Response(
                    {'message': 'E-mail já verificado anteriormente.'},
                    status=status.HTTP_200_OK
                )

            profile.is_verified = True
            profile.save()
            return Response(
                {'message': 'E-mail verificado com sucesso!'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)