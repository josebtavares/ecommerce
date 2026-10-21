"""
Backoffice do módulo Serviços — etapa 1: estado do módulo, ligar/desligar, regras, plano.
(Serviços, profissionais e agenda: etapa 2.)
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, Subscricao
from ..utils import subscricoes as subs
from ..Views.lojaView import _exige_permissao
from . import cobranca
from .models import ConfigServicos


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)


def config_payload(cfg):
    return {'confirmacao': cfg.confirmacao, 'antecedencia_min': cfg.antecedencia_min, 'dias_max': cfg.dias_max,
            'cancelar_horas': cfg.cancelar_horas, 'reembolso_fora_prazo': cfg.reembolso_fora_prazo,
            'cliente_escolhe_profissional': cfg.cliente_escolhe_profissional,
            'profissional_altera_preco': cfg.profissional_altera_preco}


def _estado(loja, membro):
    loja.refresh_from_db()
    cfg = cobranca.config(loja)
    return {**cobranca.resumo(loja), 'config': config_payload(cfg),
            'pode_gerir': membro.pode('gerir_servicos'), 'pode_pagar': membro.pode('pagar_subscricao')}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def servicos_estado(request, loja_id):
    """GET /app/loja/<loja_id>/servicos/ — o módulo: ligado?, incluído ou subscrição própria, regras, planos."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_marcacoes')
    if erro:
        return erro
    return Response(_estado(loja, membro))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def servicos_ativar(request, loja_id):
    """
    POST /app/loja/<loja_id>/servicos/ativar/ { plano_id? }   (só o dono)
    Loja em comissão sem subscrição de Serviços: escolhe o plano (1.ª vez com período de teste).
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    plano = None
    if request.data.get('plano_id') not in (None, ''):
        plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('servicos',))
        if not plano:
            return _erro('Escolhe um dos planos de Serviços disponíveis.')
    try:
        _cfg, fatura = cobranca.ativar(loja, plano)
    except (cobranca.ErroServicos, subs.ErroFatura) as e:
        return _erro(str(e))
    return Response({**_estado(loja, membro),
                     'fatura_a_pagar': subs.fatura_payload(fatura) if fatura else None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def servicos_desativar(request, loja_id):
    """POST /app/loja/<loja_id>/servicos/desativar/   (só o dono) — a subscrição acaba no fim do período pago."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    try:
        cobranca.desativar(loja)
    except cobranca.ErroServicos as e:
        return _erro(str(e))
    return Response(_estado(loja, membro))


CONFIRMACOES = dict(ConfigServicos.CONFIRMACAO)
REEMBOLSOS = dict(ConfigServicos.REEMBOLSO)
INTEIROS = {'antecedencia_min': (0, 60 * 24 * 30), 'dias_max': (1, 365), 'cancelar_horas': (0, 24 * 30)}
BOOLEANOS = ('cliente_escolhe_profissional', 'profissional_altera_preco')


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def servicos_config(request, loja_id):
    """
    PATCH /app/loja/<loja_id>/servicos/config/   (dono, gestor)
      { confirmacao, antecedencia_min, dias_max, cancelar_horas, reembolso_fora_prazo,
        cliente_escolhe_profissional, profissional_altera_preco, auto_renovar (só o dono) }
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_servicos')
    if erro:
        return erro
    dados = request.data
    cfg = cobranca.config(loja)
    campos = []
    if 'confirmacao' in dados:
        if dados['confirmacao'] not in CONFIRMACOES:
            return _erro('Confirmação inválida (auto ou manual).')
        cfg.confirmacao = dados['confirmacao']
        campos.append('confirmacao')
    if 'reembolso_fora_prazo' in dados:
        if dados['reembolso_fora_prazo'] not in REEMBOLSOS:
            return _erro('Regra de reembolso inválida (total ou nenhum).')
        cfg.reembolso_fora_prazo = dados['reembolso_fora_prazo']
        campos.append('reembolso_fora_prazo')
    for chave, (minimo, maximo) in INTEIROS.items():
        if chave in dados:
            v = dados[chave]
            if isinstance(v, bool) or not isinstance(v, (int, str)) or not str(v).strip().isdigit() \
                    or not minimo <= int(v) <= maximo:
                return _erro(f'{chave}: valor entre {minimo} e {maximo}.')
            setattr(cfg, chave, int(v))
            campos.append(chave)
    for chave in BOOLEANOS:
        if chave in dados:
            if not isinstance(dados[chave], bool):
                return _erro(f'{chave} inválido.')
            setattr(cfg, chave, dados[chave])
            campos.append(chave)
    if 'auto_renovar' in dados:
        if not membro.pode('pagar_subscricao'):
            return _erro('Só o dono da loja gere a subscrição.', status.HTTP_403_FORBIDDEN)
        if not isinstance(dados['auto_renovar'], bool):
            return _erro('auto_renovar inválido.')
        sub = Subscricao.objects.filter(loja_servicos=loja).exclude(estado='cancelada').first()
        if not sub:
            return _erro('A loja não tem subscrição de Serviços.')
        sub.auto_renovar = dados['auto_renovar']
        sub.save(update_fields=['auto_renovar', 'data_atualizacao'])
    if campos:
        cfg.save(update_fields=[*campos, 'data_atualizacao'])
    return Response(_estado(loja, membro))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def servicos_plano(request, loja_id):
    """POST /app/loja/<loja_id>/servicos/plano/ { plano_id }   (só o dono) — muda o plano a partir da renovação."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('servicos',))
    if not plano:
        return _erro('Escolhe um dos planos de Serviços disponíveis.')
    try:
        with transaction.atomic():
            sub = Subscricao.objects.select_for_update().filter(loja_servicos=loja).first()
            if not sub or sub.estado not in cobranca.ESTADOS_COM_ACESSO:
                return _erro('A loja não tem uma subscrição de Serviços activa.')
            if sub.fim_agendado:
                return _erro('A subscrição de Serviços vai terminar — volta a ligar o módulo primeiro.')
            subs.mudar_plano_sub(sub, plano)
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(_estado(loja, membro))
