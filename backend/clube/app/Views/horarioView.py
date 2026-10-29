"""
Horário das lojas (backoffice) e fuso horário da plataforma (admin do site).
A lógica está em utils/horarios.py.
"""
from zoneinfo import available_timezones

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..models import Loja, ConfiguracaoPlataforma
from ..utils import horarios
from .lojaView import _exige_permissao
from .adminView import _exige_admin


ULTIMA_ENCOMENDA = (0, 15, 30, 45, 60, 90, 120)


def _horario_loja(loja):
    return {
        'horario_ativo': loja.horario_ativo,
        'fora_horario':  loja.fora_horario,
        'dias':          horarios.semana(loja),
        'estado':        horarios.payload_publico(loja),
        'fuso':          ConfiguracaoPlataforma.atual().fuso_horario,
        'agora':         horarios.agora().strftime('%H:%M'),
        'hoje':          horarios.agora().weekday(),
        'hoje_data':     horarios.agora().date().isoformat(),
        'agendamento': {
            'ativo':        loja.agendamento_ativo,
            'intervalo':    loja.agendamento_intervalo,
            'dias':         loja.agendamento_dias,
            'antecedencia': loja.agendamento_antecedencia,
        },
        'ultima_encomenda': loja.ultima_encomenda_min,
        'excecoes':      horarios.excecoes_backoffice(loja),
        'pausa_ate':     loja.pausa_ate.isoformat() if horarios.pausa_ativa(loja) else None,
        # encomendas já agendadas para horas em que a loja agora está fechada → o editor avisa
        'agendadas_fora': horarios.agendadas_fora(loja),
    }


def _ler_agendamento(dados, loja):
    """Valida o bloco 'agendamento' do PUT. Devolve (campos, None) ou (None, mensagem)."""
    a = dados.get('agendamento')
    if a is None:
        return {}, None
    if not isinstance(a, dict):
        return None, 'Formato do agendamento inválido.'
    campos = {}
    if 'ativo' in a:
        if not isinstance(a['ativo'], bool):
            return None, 'Agendamento: ativo inválido.'
        campos['agendamento_ativo'] = a['ativo']
    try:
        if 'intervalo' in a:
            v = int(a['intervalo'])
            if v not in horarios.INTERVALOS_AGENDAMENTO:
                return None, 'Agendamento: escolhe de 15 em 15, 30 em 30, de hora a hora ou de 2 em 2 horas.'
            campos['agendamento_intervalo'] = v
        if 'dias' in a:
            v = int(a['dias'])
            if not 1 <= v <= horarios.MAX_DIAS_AGENDAMENTO:
                return None, f'Agendamento: entre 1 e {horarios.MAX_DIAS_AGENDAMENTO} dias.'
            campos['agendamento_dias'] = v
        if 'antecedencia' in a:
            v = int(a['antecedencia'])
            if not 0 <= v <= horarios.MAX_ANTECEDENCIA:
                return None, 'Agendamento: antecedência entre 0 minutos e 24 horas.'
            campos['agendamento_antecedencia'] = v
    except (TypeError, ValueError):
        return None, 'Agendamento: valor inválido.'
    return campos, None


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_horario(request, loja_id):
    """
    GET /app/loja/<loja_id>/horario/
    PUT /app/loja/<loja_id>/horario/
        { horario_ativo, fora_horario: 'agendar'|'bloquear',
          dias: [{dia: 0-6, intervalos: [{abre: 'HH:MM', fecha: 'HH:MM'}]}] }
    """
    loja = get_object_or_404(Loja.objects.select_for_update() if request.method == 'PUT' else Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'editar_loja')
    if erro:
        return erro
    if request.method == 'GET':
        return Response(_horario_loja(loja))

    dados = request.data
    ativo = dados.get('horario_ativo', loja.horario_ativo)
    if not isinstance(ativo, bool):
        return Response({'detail': 'horario_ativo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    fora = dados.get('fora_horario', loja.fora_horario)
    if fora not in dict(Loja.FORA_HORARIO):
        return Response({'detail': 'Escolhe o que acontece com a loja fechada.'}, status=status.HTTP_400_BAD_REQUEST)

    agendamento, msg = _ler_agendamento(dados, loja)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    ultima = None
    if 'ultima_encomenda' in dados:
        try:
            ultima = int(dados['ultima_encomenda'])
        except (TypeError, ValueError):
            ultima = -1
        if ultima not in ULTIMA_ENCOMENDA:
            return Response({'detail': 'Última encomenda: escolhe até ao fecho ou 15, 30, 45, 60, 90 ou 120 minutos antes.'},
                            status=status.HTTP_400_BAD_REQUEST)

    excecoes = None
    if 'excecoes' in dados:
        excecoes, msg = horarios.validar_excecoes(dados.get('excecoes'))
        if msg:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    linhas = None
    if 'dias' in dados:
        linhas, msg = horarios.validar_dias(dados.get('dias'))
        if msg:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    tem_intervalos = bool(linhas) if linhas is not None else loja.horarios.exists()
    if ativo and not tem_intervalos:
        return Response({'detail': 'Abre pelo menos um dia antes de ligar o horário.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if linhas is not None:
        horarios.guardar(loja, linhas)
    if excecoes is not None:
        horarios.guardar_excecoes(loja, excecoes)
    if ultima is not None:
        loja.ultima_encomenda_min = ultima
        agendamento['ultima_encomenda_min'] = ultima
    loja.horario_ativo, loja.fora_horario = ativo, fora
    for campo, valor in agendamento.items():
        setattr(loja, campo, valor)
    loja.save(update_fields=['horario_ativo', 'fora_horario', 'data_atualizacao', *agendamento])
    horarios.limpar_cache_fechadas()
    # serviços: marcações futuras que o horário novo (ou um dia especial) deixa fora — continuam marcadas,
    # a loja é que decide (remarcar, outro profissional ou cancelar)
    from ..servicos.agenda import fora_do_horario
    return Response({**_horario_loja(loja), 'marcacoes_fora_do_horario': fora_do_horario(loja)})


@api_view(['GET'])
@permission_classes([AllowAny])
def loja_vagas(request, loja_id):
    """
    GET /app/loja/<loja_id>/agendamento/vagas/
    Dias e horas que o cliente pode escolher para receber/levantar a encomenda.
    """
    loja = get_object_or_404(Loja.objects.prefetch_related('horarios', 'excecoes'), id=loja_id, ativa=True)
    if not loja.agendamento_ativo:
        return Response({'ativo': False, 'dias': []})
    return Response({'ativo': True, 'intervalo': loja.agendamento_intervalo, 'dias': horarios.vagas_payload(loja)})


CAMPOS_IDENTIFICACAO = ('titular_nome', 'titular_nif', 'contacto_email', 'contacto_telefone',
                        'contacto_whatsapp', 'contacto_morada', 'contacto_horario')


def _erro_identificacao(dados):
    """NIF com 9 dígitos, email e telefones com ar de válidos (ficam à vista no rodapé)."""
    import re
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email
    nif = str(dados.get('titular_nif') or '').strip()
    if nif and not re.fullmatch(r'\d{9}', nif):
        return 'O NIF tem 9 dígitos.'
    email = str(dados.get('contacto_email') or '').strip()
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return 'Email inválido.'
    for k in ('contacto_telefone', 'contacto_whatsapp'):
        tel = str(dados.get(k) or '').strip()
        if tel and not re.fullmatch(r'\+?[\d\s().-]{7,20}', tel):
            return 'Telefone inválido.' if k == 'contacto_telefone' else 'WhatsApp inválido.'
    return None


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_plataforma(request):
    """
    GET   /app/admin/plataforma/
    PATCH /app/admin/plataforma/   { fuso_horario?: 'Atlantic/Cape_Verde', subscricao_dias_teste?: 30,
                                     titular_nome?, titular_nif?, contacto_email?, contacto_telefone?,
                                     contacto_whatsapp?, contacto_morada?, contacto_horario?,
                                     mostrar_logos_pagamento?, mostrar_selo_verificada? }
    """
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    cfg = ConfiguracaoPlataforma.atual()
    if request.method == 'PATCH':
        dados = request.data
        if not any(k in dados for k in ('fuso_horario', 'subscricao_dias_teste', 'mostrar_logos_pagamento', 'mostrar_selo_verificada',
                                     *CAMPOS_IDENTIFICACAO)):
            return Response({'detail': 'Nada para mudar.'}, status=status.HTTP_400_BAD_REQUEST)
        erro = _erro_identificacao(dados)
        if erro:
            return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)
        if 'fuso_horario' in dados and not horarios.fuso_valido(dados.get('fuso_horario')):
            return Response({'detail': 'Fuso horário inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        dias = None
        if 'subscricao_dias_teste' in dados:
            try:
                dias = int(dados.get('subscricao_dias_teste'))
            except (TypeError, ValueError):
                dias = -1
            if not 0 <= dias <= 365:
                return Response({'detail': 'Dias de teste entre 0 e 365.'}, status=status.HTTP_400_BAD_REQUEST)
        cfg = ConfiguracaoPlataforma.objects.get_or_create(pk=1)[0]
        if 'fuso_horario' in dados:
            cfg.fuso_horario = dados['fuso_horario']
        if dias is not None:
            cfg.subscricao_dias_teste = dias
        for k in CAMPOS_IDENTIFICACAO:
            if k in dados:
                setattr(cfg, k, str(dados.get(k) or '').strip()[:cfg._meta.get_field(k).max_length])
        if 'mostrar_logos_pagamento' in dados:
            cfg.mostrar_logos_pagamento = dados['mostrar_logos_pagamento'] in (True, 'true', '1', 1)
        if 'mostrar_selo_verificada' in dados:
            cfg.mostrar_selo_verificada = dados['mostrar_selo_verificada'] in (True, 'true', '1', 1)
        cfg.save()
        horarios.limpar_cache_fechadas()   # com outro fuso, as lojas abertas/fechadas mudam já
    hora = timezone.now().astimezone(horarios.fuso())
    return Response({
        **{k: getattr(cfg, k) for k in CAMPOS_IDENTIFICACAO},
        'mostrar_logos_pagamento': cfg.mostrar_logos_pagamento,
        'mostrar_selo_verificada': cfg.mostrar_selo_verificada,
        'subscricao_dias_teste': cfg.subscricao_dias_teste,
        'fuso_horario': cfg.fuso_horario,
        'hora_local':   hora.strftime('%d/%m/%Y %H:%M'),
        'utc_offset':   hora.strftime('%z'),
        'fusos':        sorted(available_timezones()),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_pausa(request, loja_id):
    """
    POST /app/loja/<loja_id>/pausa/   "Fechar agora" — quem trata das encomendas (também o staff)
        { minutos: 15|30|60|120|240 }  → fecha por esse tempo
        { ate_fechar: true }           → fecha até ao fim do horário de agora
        { reabrir: true }              → acaba com a pausa
    As encomendas feitas durante a pausa seguem a regra da loja fechada (para a abertura / não aceitar).
    """
    loja = get_object_or_404(Loja.objects.select_for_update(), id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro
    dados = request.data
    if dados.get('reabrir') in (True, 'true', '1', 1):
        horarios.reabrir(loja)
    else:
        try:
            minutos = int(dados['minutos']) if dados.get('minutos') is not None else None
        except (TypeError, ValueError):
            minutos = None
        ok, msg = horarios.pausar(loja, minutos=minutos, ate_fechar=dados.get('ate_fechar') in (True, 'true', '1', 1))
        if not ok:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'pausa_ate': loja.pausa_ate.isoformat() if horarios.pausa_ativa(loja) else None,
                     'estado': horarios.payload_publico(loja)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_estado(request, loja_id):
    """GET /app/loja/<loja_id>/estado/ — aberta/fechada e pausa, para o backoffice (quem trata das encomendas)."""
    loja = get_object_or_404(Loja.objects.prefetch_related('horarios', 'excecoes'), id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro
    e = horarios.estado(loja)
    return Response({'aberta': e['aberta'], 'texto': e['texto'] or 'Aberta', 'horario_ativo': loja.horario_ativo,
                     'pausa_ate': loja.pausa_ate.isoformat() if horarios.pausa_ativa(loja) else None,
                     'pausa_hora': loja.pausa_ate.astimezone(horarios.fuso()).strftime('%H:%M') if horarios.pausa_ativa(loja) else ''})
