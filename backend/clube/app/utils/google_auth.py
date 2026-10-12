"""
Login/registo com Google — partilhado pela Bendi (utilizadorView) e pelo POS (pos/views).
Os dois usam o mesmo GOOGLE_REDIRECT_URI (a página /auth/google/callback do frontend);
o frontend distingue o destino pelo parâmetro `state`.
"""
import os
import re

import requests
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from ..models import Utilizador
from .contas import username_livre

GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/google/callback')

TIMEOUT = 10


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)




def _guardar_foto(utilizador, foto_url, google_id):
    # o Google devolve a foto a 96px — pede uma maior; uma falha aqui nunca impede o login
    foto_url = re.sub(r'=s\d+-c$', '=s400-c', foto_url)
    try:
        resp = requests.get(foto_url, timeout=5)
        if resp.ok and resp.content:
            utilizador.foto.save(f'google_{google_id}.jpg', ContentFile(resp.content), save=True)
    except Exception:
        pass


def google_obter_utilizador(code):
    """
    Troca o `code` do Google pelos dados da conta e devolve (utilizador, criado, erro).
    Procura primeiro pelo google_id e depois pelo email; cria a conta se não existir.
    `erro` é uma Response pronta a devolver (e os outros dois valores são None).
    """
    if not code:
        return None, None, _erro('Código Google em falta.')

    try:
        token_resp = requests.post('https://oauth2.googleapis.com/token', data={
            'code':          code,
            'client_id':     GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri':  GOOGLE_REDIRECT_URI,
            'grant_type':    'authorization_code',
        }, timeout=TIMEOUT)
        if token_resp.status_code != 200:
            return None, None, _erro('Erro ao obter token do Google.')

        user_resp = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {token_resp.json().get("access_token")}'},
            timeout=TIMEOUT,
        )
        if user_resp.status_code != 200:
            return None, None, _erro('Erro ao obter dados do Google.')
    except requests.RequestException:
        return None, None, _erro('O Google não respondeu. Tenta outra vez.', status.HTTP_502_BAD_GATEWAY)

    dados     = user_resp.json()
    email     = (dados.get('email') or '').strip()
    google_id = str(dados.get('id') or '')

    if not email or not google_id:
        return None, None, _erro('Email não disponível no Google.')
    # sem email verificado não se pode ligar a uma conta existente pelo email
    if not dados.get('verified_email'):
        return None, None, _erro('O email desta conta Google não está verificado.')

    criado = perfil_novo = False
    with transaction.atomic():
        utilizador = Utilizador.objects.select_related('user').filter(google_id=google_id).first()

        if utilizador is None:
            user = User.objects.filter(email__iexact=email).order_by('id').first()
            if user is None:
                user = User(
                    username=username_livre(email.split('@')[0]),
                    email=email,
                    first_name=(dados.get('given_name') or '')[:150],
                    last_name=(dados.get('family_name') or '')[:150],
                )
                user.set_unusable_password()   # entra pelo Google; pode definir password no perfil
                user.save()
                criado = True

            utilizador, perfil_novo = Utilizador.objects.get_or_create(user=user)
            if not utilizador.google_id:
                utilizador.google_id = google_id
                utilizador.save(update_fields=['google_id'])

    # fora da transação — é um pedido de rede
    if perfil_novo and dados.get('picture'):
        _guardar_foto(utilizador, dados['picture'], google_id)

    if not utilizador.is_active:
        return None, None, _erro('Conta desactivada.', status.HTTP_403_FORBIDDEN)

    return utilizador, criado, None
