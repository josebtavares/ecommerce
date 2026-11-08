"""
WebSocket do POS: ws/pos/?bilhete=... (bilhete de POST /api/pos/<id>/ws/bilhete/, uso único, 60 s).

Quem entra fica no grupo pos_<id> e recebe os avisos de utils/tempo_real_pos.py ({tipo, id, ...}, só ids):
cada aba do POS vai buscar o resto com as suas permissões.

Um membro desactivado/removido (ou o POS deixa de ser do dono) é desligado logo ao primeiro aviso da equipa
— e a página, ao saber, termina a sessão.
"""
import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache


class POSConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        query = parse_qs(self.scope.get('query_string', b'').decode())
        bilhete = (query.get('bilhete') or [None])[0]
        dados = None
        if bilhete:
            chave = f'ws_bilhete_pos:{bilhete}'
            dados = await cache.aget(chave)
            # uso único: só quem consegue apagar o bilhete entra
            if dados is None or not await cache.adelete(chave):
                dados = None
        if not dados or not await self._valido(dados):
            await self.close(code=4001)
            return
        self.pos_id = dados['pos_id']
        self.membro_id = dados.get('membro_id')
        self.user_id = dados.get('user_id')
        self.group_name = f'pos_{self.pos_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'ligado', 'pos_id': self.pos_id}))

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data == 'ping':                 # mantém a ligação viva atrás de proxies
            await self.send(text_data='pong')

    async def pos_evento(self, event):
        avisos = event.get('avisos') or []
        # mudou a equipa ou o POS: quem já não tem acesso deixa de receber
        if any(a.get('tipo') in ('equipa', 'pos') for a in avisos) and not await self._valido(
                {'pos_id': self.pos_id, 'membro_id': self.membro_id, 'user_id': self.user_id}):
            await self.send(text_data=json.dumps({'type': 'sem_acesso'}))
            await self.close(code=4003)
            return
        await self.send(text_data=json.dumps({'type': 'avisos', 'avisos': avisos}))

    @database_sync_to_async
    def _valido(self, d):
        from .models import ConfiguracaoPOS, UtilizadorPOS
        if d.get('membro_id'):
            return UtilizadorPOS.objects.filter(id=d['membro_id'], pos_id=d['pos_id'], ativo=True).exists()
        if not d.get('user_id'):
            return False
        from django.contrib.auth.models import User
        from app.autenticacao import conta_ativa
        user = User.objects.filter(pk=d['user_id']).first()
        if not user or not conta_ativa(user):
            return False
        if ConfiguracaoPOS.objects.filter(id=d['pos_id'], dono__user_id=user.pk).exists():
            return True
        # admin a ver o POS (só leitura): o bilhete foi validado por POSAuthentication há menos de 60 s
        return bool(user.is_staff)
