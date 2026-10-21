"""
Ciclo das marcações (worker processar_videos, uma vez por minuto). Idempotente: cada aviso fica
registado em Marcacao.avisos e não se repete.
  1. pendentes por pagar fora do prazo → expiradas (libertam o horário)
  2. pendentes que a loja não confirmou até à hora → expiradas; se estavam pagas, devolve-se tudo
  3. lembrete ao cliente 24 h antes (e ao profissional com conta)
  4. marcações que já acabaram há 2 h e continuam por fechar → avisa a loja (uma vez)
  5. rede de segurança: devoluções em falta (reembolso_devido > valor_reembolsado)
"""
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from . import marcacoes as ops
from .models import Marcacao

HORAS_LEMBRETE = 24
HORAS_POR_FECHAR = 2


def _marcar(m, chave):
    if chave in (m.avisos or []):
        return False
    m.avisos = [*(m.avisos or []), chave]
    Marcacao.objects.filter(pk=m.pk).update(avisos=m.avisos)
    return True


def processar(agora=None):
    from ..Views.notificacaoView import notificar
    agora = agora or timezone.now()
    r = {'expiradas': 0, 'sem_confirmacao': 0, 'lembretes': 0, 'por_fechar': 0, 'reembolsos': 0}

    r['expiradas'] = Marcacao.objects.filter(estado='pendente', pago=False, expira_em__lt=agora).update(
        estado='expirada', data_atualizacao=agora)

    for pk in Marcacao.objects.filter(estado='pendente', inicio__lte=agora).values_list('pk', flat=True)[:500]:
        with transaction.atomic():
            m = Marcacao.objects.select_for_update(of=('self',)).select_related('loja', 'profissional').get(pk=pk)
            if m.estado != 'pendente':
                continue
            m.estado = 'expirada'
            if m.pago:
                m.reembolso_devido = m.valor_pago
            m.save(update_fields=['estado', 'reembolso_devido', 'data_atualizacao'])
            ops.reembolsar(m)
            if m.cliente_id:
                notificar(utilizador=m.cliente, tipo='marcacao_atualizada', titulo='A loja não confirmou a marcação',
                          mensagem=f'{m.servico_nome} a {ops.quando_texto(m.inicio)} ficou sem efeito.'
                                   + (' O valor pago foi devolvido.' if m.pago else ''),
                          loja=m.loja, link=f'/minhas-marcacoes/{m.id}')
            r['sem_confirmacao'] += 1

    lembrar = Marcacao.objects.filter(estado='confirmada', inicio__gt=agora,
                                      inicio__lte=agora + timedelta(hours=HORAS_LEMBRETE)).select_related('loja', 'profissional__membro')
    for m in lembrar[:1000]:
        if 'lembrete' in (m.avisos or []):
            continue
        # marcada há menos de 1 h para amanhã: o cliente acabou de a ver, não é preciso lembrete
        if m.data_criacao > agora - timedelta(hours=1):
            continue
        if not _marcar(m, 'lembrete'):
            continue
        texto = f'{m.servico_nome} com {m.profissional.nome} — {ops.quando_texto(m.inicio)}, em {m.loja.nome}.'
        if m.cliente_id:
            notificar(utilizador=m.cliente, tipo='marcacao_lembrete', titulo='Lembrete: tens uma marcação', mensagem=texto,
                      loja=m.loja, link=f'/minhas-marcacoes/{m.id}')
        prof = m.profissional
        if prof.membro_id and prof.membro.ativo:
            notificar(utilizador=prof.membro.utilizador, tipo='marcacao_lembrete', titulo='Amanhã na tua agenda',
                      mensagem=f'{m.servico_nome} — {ops.quando_texto(m.inicio)} — {m.cliente_nome or (m.cliente.nome if m.cliente_id else "")}.',
                      loja=m.loja, link=f'/loja/{m.loja_id}/backoffice?seccao=servicos&marcacao={m.id}')
        r['lembretes'] += 1

    fechar = Marcacao.objects.filter(estado='confirmada', fim__lte=agora - timedelta(hours=HORAS_POR_FECHAR)).select_related('loja', 'profissional__membro')
    for m in fechar[:500]:
        if not _marcar(m, 'por_fechar'):
            continue
        ops.avisar_loja(m, 'Marcação por fechar', f'{m.servico_nome} a {ops.quando_texto(m.inicio)} — marca como concluída ou falta.')
        r['por_fechar'] += 1

    for pk in Marcacao.objects.filter(pago=True, reembolso_devido__gt=F('valor_reembolsado')).values_list('pk', flat=True)[:200]:
        with transaction.atomic():
            m = Marcacao.objects.select_for_update(of=('self',)).select_related('loja').get(pk=pk)
            if ops.reembolsar(m):
                r['reembolsos'] += 1
    return r
