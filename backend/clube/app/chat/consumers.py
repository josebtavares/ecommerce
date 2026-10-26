"""WebSocket do chat — ws/chat/?bilhete=<bilhete de POST /api/ws/bilhete/>  (ver tempo_real.py)."""
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import regras
from .models import Caixa, Conversa
from .tempo_real import grupo, destinatarios


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close(code=4001)
            return
        self.grupo = grupo(user.id)
        self._ultimo_escrever = {}
        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'grupo'):
            await self.channel_layer.group_discard(self.grupo, self.channel_name)

    # browser → servidor: só "a escrever…" (as mensagens vão por HTTP, que valida tudo)
    async def receive_json(self, conteudo, **kwargs):
        if not isinstance(conteudo, dict) or conteudo.get('tipo') != 'a_escrever':
            return
        try:
            conversa_id, caixa_id = int(conteudo.get('conversa_id')), int(conteudo.get('caixa_id'))
        except (TypeError, ValueError):
            return
        agora = time.monotonic()
        if agora - self._ultimo_escrever.get(conversa_id, 0) < 2:      # no máximo 1 aviso / 2s
            return
        self._ultimo_escrever[conversa_id] = agora
        alvo = await self._validar_escrever(conversa_id, caixa_id)
        if not alvo:
            return
        evento, uids = alvo
        for uid in uids:
            if uid != self.scope['user'].id:
                await self.channel_layer.group_send(grupo(uid), {'type': 'chat.evento', 'evento': evento})

    @database_sync_to_async
    def _validar_escrever(self, conversa_id, caixa_id):
        user = self.scope['user']
        try:
            utilizador = user.utilizador
            conversa = Conversa.objects.get(id=conversa_id)
            caixa = Caixa.objects.select_related('loja', 'utilizador__user').get(id=caixa_id)
        except Exception:
            return None
        if not regras.pode_usar(utilizador, conversa, caixa):
            return None
        nome = caixa.loja.nome if caixa.tipo == Caixa.LOJA else (
            'Suporte Bendi' if caixa.tipo == Caixa.SUPORTE else utilizador.nome)
        evento = {'tipo': 'a_escrever', 'conversa_id': conversa.id, 'caixa_id': caixa.id, 'nome': nome}
        return evento, destinatarios(conversa)

    # servidor → browser
    async def chat_evento(self, event):
        await self.send_json(event['evento'])
