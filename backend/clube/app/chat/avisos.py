"""
Avisos do chat para quem não está a ver as mensagens.

O chat em si já é em tempo real (/ws/chat/), mas quem não tem o site aberto só via o contador quando voltava.
Agora, de minuto a minuto (worker — processar_videos._avisos_horario):

• uma mensagem por ler há 5 minutos → aviso no sino, um por conversa até a pessoa ler (as mensagens seguintes
  juntam-se a esse aviso);
• ainda por ler aos 15 minutos → também um email (fila de emails, prioridade informativa), um por conversa até ler.
  Só para o cliente (e quem fala com a loja ou com o suporte a título pessoal) e para o dono/gestor da loja —
  as conversas da equipa e os agentes do suporte ficam só com o sino.

Quem silenciou a conversa não recebe nada. Ao ler, os avisos dessa conversa ficam lidos (limpar()).
Mensagens com mais de 2 horas já não geram avisos novos (ex.: as antigas, no dia em que isto entrou).
"""
from datetime import timedelta

from django.utils import timezone

from app.models import EmailEnviado, Notificacao, UtilizadorLoja
from .models import Caixa, Conversa, Mensagem

ESPERA_SINO = timedelta(minutes=5)
ESPERA_EMAIL = timedelta(minutes=15)
JANELA = timedelta(hours=2)
VALIDADE_EMAIL = timedelta(hours=12)
TIPO = 'chat_mensagem'
EQUIPA = (Conversa.EQUIPA_GRUPO, Conversa.EQUIPA_DIRETA)


def link(conversa, caixa):
    """Página que abre a conversa como esta caixa."""
    if caixa.tipo == Caixa.SUPORTE:
        return f'/admin/suporte_chat?conversa={conversa.id}'
    if caixa.tipo == Caixa.LOJA:
        return f'/loja/{caixa.loja_id}/backoffice/mensagens?conversa={conversa.id}'
    if conversa.tipo in EQUIPA:
        return f'/loja/{conversa.loja_id}/backoffice/mensagens?modo=equipa&conversa={conversa.id}'
    return f'/mensagens?caixa={caixa.id}&conversa={conversa.id}'


def pessoas(conversa, caixa):
    """[(utilizador, recebe_email)] de quem lê a conversa por esta caixa."""
    if caixa.tipo == Caixa.PESSOAL:
        u = caixa.utilizador
        if conversa.tipo in EQUIPA:
            ativo = UtilizadorLoja.objects.filter(loja_id=conversa.loja_id, utilizador=u, ativo=True).exists()
            return [(u, False)] if ativo else []
        return [(u, True)]
    if caixa.tipo == Caixa.LOJA:
        return [(m.utilizador, m.role in ('dono', 'gestor'))
                for m in UtilizadorLoja.objects.filter(loja_id=caixa.loja_id, ativo=True)
                .select_related('utilizador__user') if m.atende_chat]
    from .tempo_real import _agentes_suporte
    from app.models import Utilizador
    return [(u, False) for u in Utilizador.objects.filter(user_id__in=list(_agentes_suporte())).select_related('user')]


def _nome(caixa):
    if caixa is None or caixa.tipo == Caixa.SUPORTE:
        return 'Suporte Bendi'           # como o chat a mostra (views.perfil_caixa)
    if caixa.tipo == Caixa.LOJA:
        return caixa.loja.nome
    return caixa.utilizador.nome


def _texto(conversa, caixa, primeira, total):
    nome = _nome(primeira.remetente)
    if conversa.tipo == Conversa.EQUIPA_GRUPO:
        titulo = f'{"Nova mensagem" if total == 1 else f"{total} mensagens novas"} no grupo da equipa'
    elif caixa.tipo == Caixa.LOJA:
        titulo = f'{"Nova mensagem" if total == 1 else f"{total} mensagens novas"} de {nome} para {caixa.loja.nome}'
    else:
        titulo = f'{"Nova mensagem" if total == 1 else f"{total} mensagens novas"} de {nome}'
    if primeira.tipo == Mensagem.IMAGEM and not primeira.texto:
        excerto = f'{nome} enviou uma imagem.'
    else:
        t = ' '.join((primeira.texto or '').split())
        excerto = f'{nome}: «{t[:140]}{"…" if len(t) > 140 else ""}»'
    return titulo[:200], f'{excerto}\nResponde na Bende para continuar a conversa.'


def _por_ler(conversa, caixa, ultima_lida):
    return (conversa.mensagens.filter(id__gt=ultima_lida, apagada=False, remetente__isnull=False)
            .exclude(remetente=caixa).exclude(tipo=Mensagem.SISTEMA))


def avisar_por_ler(agora=None):
    """Corre de minuto a minuto no worker. Devolve (avisos no sino, emails na fila)."""
    from app.Views.notificacaoView import _email, notificar
    from app.utils.fila_emails import INFORMATIVO
    agora = agora or timezone.now()
    ids = set(Mensagem.objects.filter(criada_em__gte=agora - JANELA, criada_em__lte=agora - ESPERA_SINO,
                                      apagada=False, remetente__isnull=False)
              .exclude(tipo=Mensagem.SISTEMA).values_list('conversa_id', flat=True))
    sinos = emails = 0
    for conversa in Conversa.objects.filter(id__in=ids).select_related('loja') \
            .prefetch_related('participantes__caixa__loja', 'participantes__caixa__utilizador__user'):
        for p in conversa.participantes.all():
            if p.silenciada:
                continue
            novas = _por_ler(conversa, p.caixa, p.ultima_lida)
            primeira = novas.select_related('remetente__loja', 'remetente__utilizador__user').order_by('id').first()
            if not primeira or primeira.criada_em > agora - ESPERA_SINO:
                continue
            destino = link(conversa, p.caixa)
            loja = p.caixa.loja if p.caixa.tipo == Caixa.LOJA else conversa.loja
            titulo, mensagem = _texto(conversa, p.caixa, primeira, novas.count())
            manda_email = agora - JANELA <= primeira.criada_em <= agora - ESPERA_EMAIL
            for u, com_email in pessoas(conversa, p.caixa):
                if u.status != 'ativo' or not u.user.is_active:
                    continue
                if not Notificacao.objects.filter(utilizador=u, tipo=TIPO, link=destino,
                                                  data_criacao__gte=primeira.criada_em).exists():
                    notificar(u, TIPO, titulo, mensagem, loja=loja, link=destino)
                    sinos += 1
                chave = f'chat:{conversa.id}:{primeira.id}:{u.id}'
                if com_email and manda_email and not EmailEnviado.objects.filter(chave=chave).exists():
                    _email(u, TIPO, titulo, mensagem, loja, destino, INFORMATIVO, VALIDADE_EMAIL, chave)
                    emails += EmailEnviado.objects.filter(chave=chave).exists()
    return sinos, emails


def limpar(conversa, caixa):
    """A caixa leu a conversa: os avisos do chat dessa conversa ficam lidos (e o sino acerta o contador)."""
    try:
        from django.db.models import Count
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        ids = [u.id for u, _ in pessoas(conversa, caixa)]
        qs = Notificacao.objects.filter(utilizador_id__in=ids, tipo=TIPO, link=link(conversa, caixa), lida=False)
        afetados = set(qs.values_list('utilizador_id', flat=True))
        if not afetados or not qs.update(lida=True):
            return
        contas = dict(Notificacao.objects.filter(utilizador_id__in=afetados, lida=False)
                      .values('utilizador_id').annotate(n=Count('id')).values_list('utilizador_id', 'n'))
        camada = get_channel_layer()
        if camada is None:
            return
        from app.models import Utilizador
        for uid, user_id in Utilizador.objects.filter(id__in=afetados).values_list('id', 'user_id'):
            async_to_sync(camada.group_send)(f'notif_{user_id}', {'type': 'notificacao.contador',
                                                                   'nao_lidas': contas.get(uid, 0)})
    except Exception:
        pass        # o contador do sino acerta na próxima vez que abrir
