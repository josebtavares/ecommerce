"""
Admin da plataforma → secção POS.

Visão e suporte sobre todos os POS (standalone, integrado, híbrido). O dia-a-dia
(produtos, mesas, equipa) continua a ser gerido pelo dono no dashboard do POS;
aqui só se vê e se intervém em casos de suporte.

Permissões: ver_pos (lista/detalhe) · gerir_pos (acções).
"""
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, DecimalField, IntegerField, Max, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.Views.adminView import _exige_admin
from app.Views.notificacaoView import notificar
from app.utils.pagination import paginar
from app.utils.password import mensagem_password_fraca

from .models import ConfiguracaoPOS, ContaMesa, ItemContaMesa, UtilizadorPOS
from .stock import cancelar_conta

DIAS_METRICAS = 30


def _desde():
    return timezone.now() - timedelta(days=DIAS_METRICAS)


def _sub(qs, campo, agg, output):
    """Subquery agregada por POS (evita multiplicar linhas com vários joins)."""
    return Coalesce(
        Subquery(qs.filter(pos=OuterRef('pk')).values('pos').annotate(v=agg(campo)).values('v')[:1], output_field=output),
        Value(0), output_field=output,
    )


def _qs_anotado():
    desde = _desde()
    contas = ContaMesa.objects.all()
    fechadas_30d = contas.filter(status='fechada', fechada_em__gte=desde)
    dec = DecimalField(max_digits=12, decimal_places=2)
    return (ConfiguracaoPOS.objects
            .select_related('dono__user', 'loja_vinculada')
            .annotate(
                vendas_30d=_sub(fechadas_30d, 'total', Sum, dec),
                contas_30d=_sub(fechadas_30d, 'id', Count, IntegerField()),
                contas_abertas=_sub(contas.filter(status='aberta'), 'id', Count, IntegerField()),
                membros=_sub(UtilizadorPOS.objects.filter(ativo=True), 'id', Count, IntegerField()),
                ultima_atividade=Subquery(
                    contas.filter(pos=OuterRef('pk')).order_by('-criada_em').values('criada_em')[:1]
                ),
            ))


def _estado(pos):
    if pos.suspenso:
        return 'suspenso'
    return 'ativo' if pos.ativo else 'inativo'


class AdminPOSListSerializer(serializers.ModelSerializer):
    dono             = serializers.SerializerMethodField()
    loja             = serializers.SerializerMethodField()
    estado           = serializers.SerializerMethodField()
    vendas_30d       = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    contas_30d       = serializers.IntegerField(read_only=True)
    contas_abertas   = serializers.IntegerField(read_only=True)
    membros          = serializers.IntegerField(read_only=True)
    ultima_atividade = serializers.DateTimeField(read_only=True)

    class Meta:
        model  = ConfiguracaoPOS
        fields = ['id', 'nome', 'codigo_pos', 'modo', 'estado', 'ativo', 'suspenso', 'suspenso_motivo',
                  'dono', 'loja', 'vendas_30d', 'contas_30d', 'contas_abertas', 'membros',
                  'ultima_atividade', 'criado_em']

    def get_dono(self, pos):
        u = pos.dono
        return {'id': u.id, 'nome': u.nome, 'email': u.email, 'username': u.user.username} if u else None

    def get_loja(self, pos):
        l = pos.loja_vinculada
        return {'id': l.id, 'nome': l.nome} if l else None

    def get_estado(self, pos):
        return _estado(pos)


# ══════════════════════════════════════════════════════════════
# LISTA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pos_list(request):
    """
    GET /app/admin/pos/?q=&modo=&estado=ativo|inativo|suspenso&loja=com|sem&ordem=recentes|vendas|atividade
        &offset=0&limit=20
    """
    erro = _exige_admin(request, 'ver_pos')
    if erro:
        return erro

    qs = _qs_anotado()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(nome__icontains=q) | Q(codigo_pos__icontains=q) |
            Q(dono__user__username__icontains=q) | Q(dono__user__email__icontains=q) |
            Q(dono__user__first_name__icontains=q) | Q(loja_vinculada__nome__icontains=q)
        )
    modo = request.GET.get('modo')
    if modo in ('standalone', 'integrado', 'hibrido'):
        qs = qs.filter(modo=modo)
    estado = request.GET.get('estado')
    if estado == 'suspenso':
        qs = qs.filter(suspenso=True)
    elif estado == 'ativo':
        qs = qs.filter(suspenso=False, ativo=True)
    elif estado == 'inativo':
        qs = qs.filter(suspenso=False, ativo=False)
    loja = request.GET.get('loja')
    if loja == 'com':
        qs = qs.filter(loja_vinculada__isnull=False)
    elif loja == 'sem':
        qs = qs.filter(loja_vinculada__isnull=True)

    ordem = {
        'vendas':    ['-vendas_30d', '-criado_em'],
        'atividade': ['-ultima_atividade', '-criado_em'],
    }.get(request.GET.get('ordem'), ['-criado_em'])
    qs = qs.order_by(*ordem)

    response, erro = paginar(request, qs, AdminPOSListSerializer)
    if erro:
        return erro

    # resumo para os cartões do topo (sobre todos os POS, sem filtros)
    todos = ConfiguracaoPOS.objects.all()
    response.data['resumo'] = {
        'total':      todos.count(),
        'ativos':     todos.filter(suspenso=False, ativo=True).count(),
        'suspensos':  todos.filter(suspenso=True).count(),
        'por_modo':   {m: todos.filter(modo=m).count() for m in ('standalone', 'integrado', 'hibrido')},
        'vendas_30d': str(ContaMesa.objects.filter(status='fechada', fechada_em__gte=_desde())
                          .aggregate(t=Sum('total'))['t'] or 0),
        'dias':       DIAS_METRICAS,
    }
    return response


# ══════════════════════════════════════════════════════════════
# DETALHE
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pos_detalhe(request, pos_id):
    """GET /app/admin/pos/<pos_id>/"""
    erro = _exige_admin(request, 'ver_pos')
    if erro:
        return erro

    pos = get_object_or_404(_qs_anotado(), id=pos_id)
    desde = _desde()
    fechadas = ContaMesa.objects.filter(pos=pos, status='fechada', fechada_em__gte=desde)

    vendas_dia = (fechadas.annotate(dia=TruncDate('fechada_em')).values('dia')
                  .annotate(total=Sum('total'), contas=Count('id')).order_by('dia'))
    # unidades vendidas sozinhas + dentro de menus (a cozinha serviu-as na mesma)
    from ..utils.conjuntos import vendas_por_produto
    itens = (ItemContaMesa.objects.filter(conta__in=fechadas).exclude(status='cancelado')
             .values_list('produto_pos_id', 'produto_pos__nome', 'produto_id', 'produto__nome',
                          'quantidade', 'preco_unitario', 'componentes'))
    top = [{'nome': p['nome'], 'qtd': p['qty'], 'total': f"{p['valor']:.2f}",
            'qty_conjuntos': p['qty_conjuntos']}
           for p in vendas_por_produto(
               ('pos', pp, ppn, q, preco, comps) if pp else ('loja', lp, lpn, q, preco, comps)
               for pp, ppn, lp, lpn, q, preco, comps in itens)[:8]]
    abertas = (ContaMesa.objects.filter(pos=pos, status='aberta').select_related('mesa', 'atendente')
               .annotate(n_items=Count('items', filter=~Q(items__status='cancelado'))).order_by('criada_em'))
    historico = (ContaMesa.objects.filter(pos=pos).exclude(status='aberta').select_related('mesa')
                 .order_by('-atualizada_em')[:15])

    n_contas = pos.contas_30d or 0
    data = AdminPOSListSerializer(pos).data
    data.update({
        'taxa_servico_ativa': pos.taxa_servico_ativa,
        'taxa_servico_percentagem': str(pos.taxa_servico_percentagem),
        'suspenso_em': pos.suspenso_em,
        'produtos_proprios': pos.produtos_pos.count(),
        'mesas': pos.mesas.count(),
        'ticket_medio_30d': str(round(pos.vendas_30d / n_contas, 2)) if n_contas else '0.00',
        'vendas_por_dia': [{'dia': v['dia'], 'total': str(v['total']), 'contas': v['contas']} for v in vendas_dia],
        'top_produtos': [{'nome': t['nome'], 'quantidade': t['qtd'], 'total': t['total'],
                          'em_menus': t['qty_conjuntos']} for t in top],
        'equipa': [
            {'id': m.id, 'nome': m.nome, 'username': m.username_pos, 'papel': m.papel, 'ativo': m.ativo}
            for m in pos.staff.all().order_by('nome')
        ],
        'contas_abertas_lista': [
            {'id': c.id, 'mesa': getattr(c.mesa, 'numero', None), 'total': str(c.total),
             'itens': c.n_items, 'atendente': c.atendente_nome or getattr(c.atendente, 'nome', None), 'criada_em': c.criada_em}
            for c in abertas
        ],
        'historico': [
            {'id': c.id, 'mesa': getattr(c.mesa, 'numero', None), 'total': str(c.total), 'status': c.status,
             'metodo_pagamento': c.metodo_pagamento, 'data': c.fechada_em or c.atualizada_em}
            for c in historico
        ],
    })
    return Response(data)


# ══════════════════════════════════════════════════════════════
# ACÇÕES DE SUPORTE
# ══════════════════════════════════════════════════════════════

def _notificar_dono(pos, tipo, titulo, mensagem):
    if pos.dono_id:
        notificar(utilizador=pos.dono, tipo=tipo, titulo=titulo, mensagem=mensagem, link='/pos/dashboard')


def suspender_pos(pos, motivo):
    """Suspende o POS e avisa o dono (também usado ao suspender a loja vinculada)."""
    pos.suspenso, pos.suspenso_motivo, pos.suspenso_em = True, motivo, timezone.now()
    pos.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em', 'atualizado_em'])
    _notificar_dono(pos, 'pos_suspenso', f'POS "{pos.nome}" suspenso',
                    f'O teu POS foi suspenso pela plataforma. Motivo: {motivo}')


def reativar_pos(pos):
    pos.suspenso, pos.suspenso_motivo, pos.suspenso_em = False, '', None
    pos.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em', 'atualizado_em'])
    _notificar_dono(pos, 'pos_reativado', f'POS "{pos.nome}" reactivado', 'O teu POS voltou a estar operacional.')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_pos_suspender(request, pos_id):
    """POST /app/admin/pos/<pos_id>/suspender/   Body: { motivo }"""
    erro = _exige_admin(request, 'gerir_pos')
    if erro:
        return erro
    pos = get_object_or_404(ConfiguracaoPOS.objects.select_for_update(), id=pos_id)
    motivo = str(request.data.get('motivo') or '').strip()[:300]
    if not motivo:
        return Response({'detail': 'Indica o motivo da suspensão (é mostrado ao dono).'}, status=status.HTTP_400_BAD_REQUEST)
    if pos.suspenso:
        return Response({'detail': 'O POS já está suspenso.'}, status=status.HTTP_400_BAD_REQUEST)

    suspender_pos(pos, motivo)
    return Response({'detail': 'POS suspenso.', 'estado': _estado(pos)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_pos_reativar(request, pos_id):
    """POST /app/admin/pos/<pos_id>/reativar/"""
    erro = _exige_admin(request, 'gerir_pos')
    if erro:
        return erro
    pos = get_object_or_404(ConfiguracaoPOS.objects.select_for_update(), id=pos_id)
    if not pos.suspenso:
        return Response({'detail': 'O POS não está suspenso.'}, status=status.HTTP_400_BAD_REQUEST)
    from ..utils.moderacao import recusa_reativar
    recusa = recusa_reativar(pos.dono_id, pos.suspenso_motivo)
    if recusa:
        return Response({'detail': recusa}, status=status.HTTP_400_BAD_REQUEST)
    from ..utils.subscricoes import MOTIVO_SUSPENSAO
    if pos.suspenso_motivo.startswith(MOTIVO_SUSPENSAO):
        # reactivar à mão deixava o POS a funcionar sem pagar (o ciclo já não volta a suspendê-lo)
        return Response({'detail': 'Este POS foi suspenso por falta de pagamento da subscrição — vai a Subscrições → POS '
                                   'e marca a fatura como paga, adia-a ou oferece meses: o POS volta sozinho.'},
                        status=status.HTTP_400_BAD_REQUEST)

    reativar_pos(pos)
    return Response({'detail': 'POS reactivado.', 'estado': _estado(pos)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_pos_desligar_loja(request, pos_id):
    """POST /app/admin/pos/<pos_id>/desligar-loja/ → volta a standalone (produtos do POS mantêm-se)"""
    erro = _exige_admin(request, 'gerir_pos')
    if erro:
        return erro
    pos = get_object_or_404(ConfiguracaoPOS.objects.select_for_update(), id=pos_id)
    if not pos.loja_vinculada_id:
        return Response({'detail': 'Este POS não está ligado a nenhuma loja.'}, status=status.HTTP_400_BAD_REQUEST)
    if ContaMesa.objects.filter(pos=pos, status='aberta', items__produto__isnull=False).exists():
        return Response({'detail': 'Há contas abertas com produtos da loja. Fecha-as ou cancela-as primeiro.'},
                        status=status.HTTP_400_BAD_REQUEST)

    loja_nome = pos.loja_vinculada.nome
    pos.desconectar_loja()
    from ..utils.subscricoes_pos import sincronizar_pos
    # depois do commit: aqui o POS está bloqueado e o ciclo bloqueia subscrição → POS (sem impasses)
    transaction.on_commit(lambda: sincronizar_pos(pos))   # se estava no plano Loja + POS: 30 dias até ao seu plano
    _notificar_dono(pos, 'pos_admin', f'POS "{pos.nome}" desligado da loja',
                    f'A plataforma desligou o POS da loja "{loja_nome}". O POS passou a standalone.')
    return Response({'detail': 'Loja desligada. O POS passou a standalone.', 'modo': pos.modo})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_pos_cancelar_conta(request, pos_id, conta_id):
    """POST /app/admin/pos/<pos_id>/contas/<conta_id>/cancelar/   Body: { motivo }"""
    erro = _exige_admin(request, 'gerir_pos')
    if erro:
        return erro
    conta = get_object_or_404(ContaMesa.objects.select_for_update(), id=conta_id, pos_id=pos_id)
    if conta.status != 'aberta':
        return Response({'detail': 'A conta já está fechada/cancelada.'}, status=status.HTTP_400_BAD_REQUEST)

    motivo = str(request.data.get('motivo') or '').strip()[:250]
    cancelar_conta(conta, f'[Admin] {motivo}'.strip(), por='Bendi (suporte)')
    return Response({'detail': 'Conta cancelada. Stock reposto e mesa libertada.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_pos_membro_password(request, pos_id, membro_id):
    """POST /app/admin/pos/<pos_id>/membros/<membro_id>/password/   Body: { nova_password }"""
    erro = _exige_admin(request, 'gerir_pos')
    if erro:
        return erro
    membro = get_object_or_404(UtilizadorPOS, id=membro_id, pos_id=pos_id)
    nova = str(request.data.get('nova_password') or '')
    msg = mensagem_password_fraca(nova)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    membro.set_password(nova)
    membro.save(update_fields=['password_pos'])
    _notificar_dono(membro.pos, 'pos_admin', 'Password de membro redefinida',
                    f'A plataforma redefiniu a password de {membro.nome} ({membro.username_pos}) no POS "{membro.pos.nome}".')
    return Response({'detail': f'Password de {membro.nome} redefinida.'})


# ══════════════════════════════════════════════════════════════
# VER O POS (SÓ LEITURA)
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_pos_ver(request, pos_id):
    """
    GET  /app/admin/pos/<pos_id>/ver/  → últimos acessos de admins a este POS
    POST /app/admin/pos/<pos_id>/ver/  → regista o acesso e devolve o token de leitura
    O dashboard como o dono o vê, sem a password dele, também com o POS suspenso ou o dono
    banido (utils/ver_loja.py).
    """
    from .models import AcessoAdminPOS
    from ..utils.ver_loja import emitir_token_pos, DURACAO
    from ..utils.horarios import fuso
    erro = _exige_admin(request, 'ver_backoffice_lojas')
    if erro:
        return erro
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id)
    if request.method == 'POST':
        AcessoAdminPOS.objects.create(pos=pos, pos_nome=pos.nome, admin=request.user,
                                      admin_nome=request.user.username, ip=request.META.get('REMOTE_ADDR') or None)
        return Response({'token': emitir_token_pos(request.user, pos), 'pos': pos.id,
                         'minutos': int(DURACAO.total_seconds() // 60)})
    acessos = AcessoAdminPOS.objects.filter(pos=pos)[:20]
    return Response({'acessos': [{'id': a.id, 'admin': a.admin_nome, 'quando': a.criado_em.astimezone(fuso()).strftime('%d/%m/%Y %H:%M')}
                                 for a in acessos]})
