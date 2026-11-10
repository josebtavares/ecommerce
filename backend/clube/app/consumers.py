# app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# O chat (caixas de mensagens) tem o consumer próprio em app/chat/consumers.py


# ═══════════════════════════════════════════════════════════════
# Notificações em tempo real
# ═══════════════════════════════════════════════════════════════
class NotificacaoConsumer(AsyncWebsocketConsumer):
    """
    Canal pessoal de notificações de cada utilizador.
    URL: ws/notificacoes/

    Ao conectar envia logo o contador de não lidas.
    Quando o backend chama notificar(), a notificação chega
    aqui em tempo real sem polling.
    """

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(code=4001)
            return

        self.group_name = f"notif_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # envia contador de não lidas ao conectar
        count = await self._nao_lidas(user)
        await self.send(text_data=json.dumps({
            "type":      "contador",
            "nao_lidas": count,
        }))

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    # backend → browser: nova notificação
    async def notificacao_nova(self, event):
        await self.send(text_data=json.dumps({
            "type":        "nova",
            "notificacao": event["notificacao"],
            "nao_lidas":   event.get("nao_lidas", 0),
        }))

    # backend → browser: só actualiza o badge
    async def reembolso_atualizado(self, event):
        # pedido de reembolso mudou (mensagem, estado…): só ids — a página aberta vai buscar o resto
        await self.send(text_data=json.dumps({'type': 'reembolso', 'reembolso': event['reembolso']}))

    async def marcacao_atualizada(self, event):
        # marcação de serviços mudou (mensagem, proposta, estado…): só ids — a página aberta vai buscar o resto
        await self.send(text_data=json.dumps({'type': 'marcacao', 'marcacao': event['marcacao']}))

    async def encomenda_atualizada(self, event):
        # encomenda ou entrega mudou (estado, fatura, condutor…): só ids — a página aberta vai buscar o resto
        await self.send(text_data=json.dumps({'type': 'encomenda', 'encomenda': event['encomenda']}))

    async def subscricao_atualizada(self, event):
        # mensalidade, subscrição ou fatura da Bendi mudou: só ids ({tipo, id, loja_id, pos_id})
        await self.send(text_data=json.dumps({'type': 'subscricao', 'subscricao': event['subscricao']}))

    async def faturacao_atualizada(self, event):
        # fatura de uma venda registada/anulada, ou venda que passou a faturável: só ids ({origem, id, loja_id, pos_id})
        await self.send(text_data=json.dumps({'type': 'faturacao', 'faturacao': event['faturacao']}))

    async def painel_atualizado(self, event):
        # algo mudou nos números da plataforma (Dashboard/Relatórios do admin): só {origem}
        await self.send(text_data=json.dumps({'type': 'painel', 'painel': event['painel']}))

    async def lista_atualizada(self, event):
        # uma lista mudou (produtos, inventário, lojas, utilizadores…): só {origem, loja_id} — utils/tempo_real_listas.py
        await self.send(text_data=json.dumps({'type': 'lista', 'lista': event['lista']}))

    async def notificacao_contador(self, event):
        await self.send(text_data=json.dumps({
            "type":      "contador",
            "nao_lidas": event["nao_lidas"],
        }))

    @database_sync_to_async
    def _nao_lidas(self, user):
        from .models import Notificacao
        try:
            return Notificacao.objects.filter(
                utilizador=user.utilizador, lida=False
            ).count()
        except Exception:
            return 0