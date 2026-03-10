# app/Views/password_reset.py  (exemplo)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

token_generator = PasswordResetTokenGenerator()

from django.shortcuts import render
from django.http import JsonResponse
from ..models import Utilizador
from ..Serializers.UtilizadorSerializer import PasswordResetRequestSerializer, PasswordResetConfirmSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
# … resto das imports e das views
# views/password_reset.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    try:
        user = Utilizador.objects.get(email=email)
    except Utilizador.DoesNotExist:
        # Para evitar enumeração de e-mails devolve sempre 200
        return Response(status=status.HTTP_200_OK)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)

    reset_link = f'http://192.168.0.110:8080/recuperar_senha?uid={uid}&token={token}'

    send_mail(
        subject='Recuperação de palavra-passe',
        message=f'Clique no link para redefinir a sua palavra-passe: {reset_link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uid = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = Utilizador.objects.get(pk=user_id)
    except (ValueError, Utilizador.DoesNotExist):
        return Response({'detail': 'Link inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_generator.check_token(user, token):
        return Response({'detail': 'Token expirado ou inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({'detail': 'Palavra-passe actualizada com sucesso.'}, status=status.HTTP_200_OK)
