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


def sincronizar_loja(loja):
    """
    A loja deixou de aceitar marcações (fechada pelo dono, suspensa pela plataforma, módulo Serviços
    parado ou por pagar): avisa os clientes com marcações futuras — continuam marcadas e podem
    cancelá-las com devolução total. Quando volta: avisa os mesmos clientes. Uma vez por mudança
    (Marcacao.avisos 'loja_indisponivel'). Devolve quantos clientes avisou.
    """
    from ..Views.notificacaoView import notificar
    from .cobranca import disponivel
    loja = type(loja).objects.select_related('config_servicos').get(pk=loja.pk)
    aberta = disponivel(loja)
    futuras = Marcacao.objects.filter(loja=loja, estado__in=Marcacao.ATIVOS, inicio__gt=timezone.now(),
                                      cliente__isnull=False).select_related('cliente')
    n = 0
    for m in futuras[:2000]:
        avisado = 'loja_indisponivel' in (m.avisos or [])
        if not aberta and not avisado:
            _marcar(m, 'loja_indisponivel')
            notificar(utilizador=m.cliente, tipo='marcacao_atualizada', titulo=f'{loja.nome} está fechada de momento',
                      mensagem=f'A tua marcação ({m.servico_nome}, {ops.quando_texto(m.inicio)}) continua marcada. '
                               'Se preferires, podes cancelá-la com devolução total.',
                      loja=loja, link=f'/minhas-marcacoes/{m.id}')
            n += 1
        elif aberta and avisado:
            m.avisos = [a for a in m.avisos if a != 'loja_indisponivel']
            Marcacao.objects.filter(pk=m.pk).update(avisos=m.avisos)
            notificar(utilizador=m.cliente, tipo='marcacao_atualizada', titulo=f'{loja.nome} voltou a abrir',
                      mensagem=f'A tua marcação ({m.servico_nome}, {ops.quando_texto(m.inicio)}) mantém-se.',
                      loja=loja, link=f'/minhas-marcacoes/{m.id}')
            n += 1
    return n


def sincronizar_depois(loja):
    """Para chamar dentro de uma transacção (mudar o estado da loja…): avisa só se ela for confirmada."""
    transaction.on_commit(lambda: sincronizar_loja(loja))


def processar(agora=None):
    from ..Views.notificacaoView import notificar
    agora = agora or timezone.now()
    r = {'expiradas': 0, 'sem_confirmacao': 0, 'lembretes': 0, 'por_fechar': 0, 'reembolsos': 0, 'avisos_loja': 0}

    r['expiradas'] = ops.expirar_vencidas()

    for pk in Marcacao.objects.filter(estado='pendente', inicio__lte=agora).values_list('pk', flat=True)[:500]:
        with transaction.atomic():
            m = Marcacao.objects.select_for_update(of=('self',)).select_related('loja', 'profissional').get(pk=pk)
            if m.estado != 'pendente':
                continue
            m.estado = 'expirada'
            if m.pago:
                m.reembolso_devido = m.valor_pago
            m.save(update_fields=['estado', 'reembolso_devido', 'data_atualizacao'])
            ops.anular_propostas(m)
            devolvido = ops.reembolsar(m)
            if m.cliente_id:
                notificar(utilizador=m.cliente, tipo='marcacao_atualizada', titulo='A loja não confirmou a marcação',
                          mensagem=f'{m.servico_nome} a {ops.quando_texto(m.inicio)} ficou sem efeito.'
                                   + (' O valor pago foi devolvido.' if devolvido else ''),
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
                      loja=m.loja, link=f'/loja/{m.loja_id}/backoffice/servicos?marcacao={m.id}')
        r['lembretes'] += 1

    fechar = Marcacao.objects.filter(estado='confirmada', fim__lte=agora - timedelta(hours=HORAS_POR_FECHAR)).select_related('loja', 'profissional__membro')
    for m in fechar[:500]:
        if not _marcar(m, 'por_fechar'):
            continue
        ops.avisar_loja(m, 'Marcação por fechar', f'{m.servico_nome} a {ops.quando_texto(m.inicio)} — marca como concluída ou falta.')
        r['por_fechar'] += 1

    # rede de segurança: qualquer mudança (subscrição suspensa, módulo, estado da loja) chega aos clientes num minuto
    from ..models import Loja
    for loja in Loja.objects.filter(marcacoes__estado__in=Marcacao.ATIVOS, marcacoes__inicio__gt=agora).distinct()[:500]:
        r['avisos_loja'] += sincronizar_loja(loja)

    # as recusadas pelo fornecedor (reembolso_erro) seguem as esperas de marcacoes.reembolsos_por_concluir
    for pk in Marcacao.objects.filter(pago=True, reembolso_erro='', reembolso_devido__gt=F('valor_reembolsado')).values_list('pk', flat=True)[:200]:
        with transaction.atomic():
            m = Marcacao.objects.select_for_update(of=('self',)).select_related('loja').get(pk=pk)
            if ops.reembolsar(m):
                r['reembolsos'] += 1
    return r
