"""
Backoffice do módulo Serviços — etapa 2: serviços, profissionais (horário, ausências), agenda,
marcações manuais, remarcar / reatribuir / confirmar / cancelar.

Permissões: gerir_servicos (dono, gestor) cria e muda serviços e profissionais;
gerir_marcacoes (dono, gestor, staff) vê a agenda toda e gere as marcações; um profissional
ligado a uma conta sem gerir_marcacoes vê só a sua agenda.
"""
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, UtilizadorLoja
from ..uploads import validar_ficheiro
from ..utils import limpeza
from ..utils.dinheiro import formatar, ler_valor
from ..utils.horarios import fuso
from ..Views.lojaView import _get_membro
from . import agenda, cobranca
from .marcacoes import ErroMarcacao, marcacao_payload
from . import marcacoes as ops
from .models import AusenciaProfissional, HorarioProfissional, Marcacao, Profissional, Servico, ServicoImagem

MAX_IMAGENS = 6


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST, **extra):
    return Response({'detail': msg, **extra}, status=codigo)


def _acesso(request, loja_id, permissao):
    """(loja, membro, None) ou (None, None, Response)."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _get_membro(request, loja)
    if not membro or not membro.pode(permissao):
        return None, None, _erro(f'Sem permissão: {permissao}', status.HTTP_403_FORBIDDEN)
    return loja, membro, None


def _quem(membro):
    nome = membro.utilizador.nome or membro.utilizador.user.username
    return f'{nome} ({membro.get_role_display().lower()})'


def _url(request, f):
    return request.build_absolute_uri(f.url) if f else None


def _texto(dados, chave, maximo, obrigatorio=False, nome=None):
    v = dados.get(chave)
    if v is None:
        return ('', None) if not obrigatorio else (None, f'{nome or chave} é obrigatório.')
    if not isinstance(v, str):
        return None, f'{nome or chave} inválido.'
    v = v.strip()
    if obrigatorio and not v:
        return None, f'{nome or chave} é obrigatório.'
    if len(v) > maximo:
        return None, f'{nome or chave}: no máximo {maximo} caracteres.'
    return v, None


def _inteiro(v, minimo, maximo):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        n = v
    elif isinstance(v, str) and v.strip().isdigit() and len(v.strip()) < 7:
        n = int(v)
    else:
        return None
    return n if minimo <= n <= maximo else None


def _ler_dt(v):
    """ISO (com ou sem fuso; sem fuso = hora de Cabo Verde) → datetime aware, ou None."""
    if not isinstance(v, str) or len(v) > 40:
        return None
    try:
        dt = datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=fuso())
    return dt


def _ler_dia(v):
    try:
        return date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════
# SERVIÇOS (catálogo)
# ══════════════════════════════════════════════════════════════

def servico_payload(s, request):
    return {'id': s.id, 'nome': s.nome, 'descricao': s.descricao, 'categoria': s.categoria,
            'duracao_min': s.duracao_min, 'intervalo_min': s.intervalo_min, 'tipo_preco': s.tipo_preco,
            'preco': str(s.preco), 'preco_texto': ('a partir de ' if s.tipo_preco == 'a_partir' else '') + formatar(s.preco),
            'pagamento': s.pagamento, 'ativo': s.ativo, 'ordem': s.ordem,
            'profissionais': [p.id for p in s.profissionais.all()],
            'imagens': [{'id': i.id, 'url': _url(request, i.ficheiro)} for i in s.imagens.all()]}


def _ler_servico(loja, dados, atual=None):
    campos, profs = {}, None
    if 'nome' in dados or atual is None:
        v, e = _texto(dados, 'nome', 120, True, 'O nome')
        if e:
            return None, None, e
        campos['nome'] = v
    for chave, maximo in (('descricao', 2000), ('categoria', 80)):
        if chave in dados:
            v, e = _texto(dados, chave, maximo)
            if e:
                return None, None, e
            campos[chave] = v
    if 'duracao_min' in dados or atual is None:
        n = _inteiro(dados.get('duracao_min'), 5, 720)
        if n is None:
            return None, None, 'Duração inválida (entre 5 minutos e 12 horas).'
        campos['duracao_min'] = n
    if 'intervalo_min' in dados:
        n = _inteiro(dados.get('intervalo_min'), 0, 240)
        if n is None:
            return None, None, 'Intervalo inválido (0 a 240 minutos).'
        campos['intervalo_min'] = n
    if 'tipo_preco' in dados:
        if dados['tipo_preco'] not in dict(Servico.TIPOS_PRECO):
            return None, None, 'Tipo de preço inválido (fixo ou a_partir).'
        campos['tipo_preco'] = dados['tipo_preco']
    if 'preco' in dados or atual is None:
        v, e = ler_valor(dados.get('preco'), 'O preço')
        if e:
            return None, None, e
        campos['preco'] = v
    if 'pagamento' in dados:
        if dados['pagamento'] not in dict(Servico.PAGAMENTOS):
            return None, None, 'Forma de pagamento inválida.'
        campos['pagamento'] = dados['pagamento']
    if 'ativo' in dados:
        if not isinstance(dados['ativo'], bool):
            return None, None, 'ativo inválido.'
        campos['ativo'] = dados['ativo']
    if 'ordem' in dados:
        n = _inteiro(dados.get('ordem'), 0, 999)
        if n is None:
            return None, None, 'Ordem inválida.'
        campos['ordem'] = n
    if 'profissionais' in dados:
        ids = dados.get('profissionais')
        if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids) or len(ids) > 200:
            return None, None, 'Lista de profissionais inválida.'
        profs = list(Profissional.objects.filter(loja=loja, id__in=ids))
        if len(profs) != len(set(ids)):
            return None, None, 'Há profissionais que não são desta loja.'
    return campos, profs, None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def catalogo(request, loja_id):
    """GET/POST /app/loja/<id>/servicos/catalogo/"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes' if request.method == 'GET' else 'gerir_servicos')
    if erro:
        return erro
    if request.method == 'POST':
        campos, profs, msg = _ler_servico(loja, request.data)
        if msg:
            return _erro(msg)
        s = Servico.objects.create(loja=loja, **campos)
        if profs is None:                           # sem lista: todos os profissionais activos
            profs = list(loja.profissionais.filter(ativo=True))
        s.profissionais.set(profs)
        return Response(servico_payload(s, request), status=status.HTTP_201_CREATED)
    qs = loja.servicos.prefetch_related('profissionais', 'imagens')
    return Response([servico_payload(s, request) for s in qs])


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def catalogo_item(request, loja_id, servico_id):
    """PATCH/DELETE /app/loja/<id>/servicos/catalogo/<sid>/ — com marcações não se apaga: fica inactivo."""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    s = get_object_or_404(Servico, id=servico_id, loja=loja)
    if request.method == 'DELETE':
        if s.marcacoes.exists():
            s.ativo = False
            s.save(update_fields=['ativo', 'data_atualizacao'])
            return Response({'apagado': False, 'desativado': True, 'servico': servico_payload(s, request),
                             'detail': 'Este serviço tem marcações — ficou inactivo (deixa de aparecer aos clientes).'})
        s.delete()
        return Response({'apagado': True})
    campos, profs, msg = _ler_servico(loja, request.data, s)
    if msg:
        return _erro(msg)
    for k, v in campos.items():
        setattr(s, k, v)
    s.save()
    if profs is not None:
        s.profissionais.set(profs)
    return Response(servico_payload(s, request))


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def catalogo_imagem(request, loja_id, servico_id):
    """POST /app/loja/<id>/servicos/catalogo/<sid>/imagens/  (multipart: ficheiro)"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    s = get_object_or_404(Servico, id=servico_id, loja=loja)
    f = request.FILES.get('ficheiro')
    if not f:
        return _erro('Escolhe uma imagem.')
    if s.imagens.count() >= MAX_IMAGENS:
        return _erro(f'No máximo {MAX_IMAGENS} imagens por serviço.')
    from django.core.exceptions import ValidationError
    try:
        validar_ficheiro(ServicoImagem._meta.get_field('ficheiro'), f)
    except ValidationError as e:
        return _erro(e.messages[0])
    ServicoImagem.objects.create(servico=s, ficheiro=f, ordem=s.imagens.count())
    return Response(servico_payload(s, request), status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def catalogo_imagem_apagar(request, loja_id, imagem_id):
    """DELETE /app/loja/<id>/servicos/imagens/<iid>/"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    img = get_object_or_404(ServicoImagem, id=imagem_id, servico__loja=loja)
    s = img.servico
    img.delete()                                  # o ficheiro vai para a fila de limpeza (signals)
    return Response(servico_payload(s, request))


# ══════════════════════════════════════════════════════════════
# PROFISSIONAIS
# ══════════════════════════════════════════════════════════════

def profissional_payload(p, request):
    m = p.membro
    return {'id': p.id, 'nome': p.nome, 'descricao': p.descricao, 'foto': _url(request, p.foto), 'ativo': p.ativo,
            'ordem': p.ordem,
            'membro': {'id': m.id, 'nome': m.utilizador.nome or m.utilizador.user.username, 'role': m.role} if m else None,
            'horario': [{'dia_semana': h.dia_semana, 'inicio': h.inicio.strftime('%H:%M'), 'fim': h.fim.strftime('%H:%M')}
                        for h in p.horarios.all()],
            'servicos': [s.id for s in p.servicos.all()]}


def _futuras(prof):
    return Marcacao.objects.filter(profissional=prof, estado__in=Marcacao.ATIVOS, inicio__gte=_agora())


def _agora():
    from django.utils import timezone
    return timezone.now()


def _lista_curta(qs):
    return [marcacao_payload(m) for m in qs.select_related('profissional', 'cliente__user')[:50]]


def _ler_membro(loja, v, atual=None):
    """membro_id → (UtilizadorLoja | None, erro)."""
    if v in (None, ''):
        return None, None
    if isinstance(v, bool) or not isinstance(v, int):
        return None, 'membro inválido.'
    m = UtilizadorLoja.objects.filter(loja=loja, id=v, ativo=True).select_related('utilizador__user').first()
    if not m:
        return None, 'Esse membro não é da equipa desta loja.'
    outro = Profissional.objects.filter(membro=m).exclude(pk=atual.pk if atual else None).first()
    if outro:
        return None, f'Essa conta já está ligada ao profissional {outro.nome}.'
    return m, None


def _limite_profissionais(loja, excluir=None):
    lim = cobranca.limites(loja)['profissionais']
    if not lim:
        return None
    n = loja.profissionais.filter(ativo=True).exclude(pk=excluir).count()
    if n >= lim:
        return (f'O teu plano de Serviços inclui até {lim} profissional(is) activo(s). '
                'Desactiva outro ou muda de plano em Subscrição.')
    return None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profissionais(request, loja_id):
    """GET/POST /app/loja/<id>/servicos/profissionais/  { nome, descricao?, membro_id?, servicos? }"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes' if request.method == 'GET' else 'gerir_servicos')
    if erro:
        return erro
    if request.method == 'GET':
        qs = loja.profissionais.select_related('membro__utilizador__user').prefetch_related('horarios', 'servicos')
        equipa = UtilizadorLoja.objects.filter(loja=loja, ativo=True).select_related('utilizador__user')
        return Response({
            'profissionais': [profissional_payload(p, request) for p in qs],
            # para ligar uma conta: os membros da equipa ainda sem ficha
            'equipa': [{'id': m.id, 'nome': m.utilizador.nome or m.utilizador.user.username, 'role': m.role,
                        'ligado': hasattr(m, 'profissional')} for m in equipa],
            'limites': cobranca.limites(loja),
        })
    nome, e = _texto(request.data, 'nome', 100, True, 'O nome')
    if e:
        return _erro(e)
    desc, e = _texto(request.data, 'descricao', 300)
    if e:
        return _erro(e)
    m, e = _ler_membro(loja, request.data.get('membro_id'))
    if e:
        return _erro(e)
    e = _limite_profissionais(loja)
    if e:
        return _erro(e)
    p = Profissional.objects.create(loja=loja, nome=nome, descricao=desc, membro=m, ordem=loja.profissionais.count())
    ids = request.data.get('servicos')
    if isinstance(ids, list) and all(isinstance(i, int) for i in ids):
        p.servicos.set(Servico.objects.filter(loja=loja, id__in=ids))
    return Response(profissional_payload(p, request), status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def profissional(request, loja_id, prof_id):
    """
    PATCH  /app/loja/<id>/servicos/profissionais/<pid>/ { nome, descricao, membro_id, ativo, ordem, servicos }
    DELETE — só sem marcações (senão desactiva-se). Desactivar com marcações futuras → 409 com a lista.
    """
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    p = get_object_or_404(Profissional, id=prof_id, loja=loja)
    if request.method == 'DELETE':
        futuras = _futuras(p)
        if futuras.exists():
            return _erro('Este profissional tem marcações futuras — reatribui-as ou cancela-as primeiro.',
                         status.HTTP_409_CONFLICT, marcacoes=_lista_curta(futuras))
        if p.marcacoes.exists():
            p.ativo = False
            p.save(update_fields=['ativo'])
            return Response({'apagado': False, 'desativado': True, 'profissional': profissional_payload(p, request),
                             'detail': 'Tem histórico de marcações — ficou inactivo.'})
        p.delete()
        return Response({'apagado': True})
    d = request.data
    campos = []
    if 'nome' in d:
        v, e = _texto(d, 'nome', 100, True, 'O nome')
        if e:
            return _erro(e)
        p.nome = v
        campos.append('nome')
    if 'descricao' in d:
        v, e = _texto(d, 'descricao', 300)
        if e:
            return _erro(e)
        p.descricao = v
        campos.append('descricao')
    if 'membro_id' in d:
        m, e = _ler_membro(loja, d.get('membro_id'), p)
        if e:
            return _erro(e)
        p.membro = m
        campos.append('membro')
    if 'ordem' in d:
        n = _inteiro(d.get('ordem'), 0, 999)
        if n is None:
            return _erro('Ordem inválida.')
        p.ordem = n
        campos.append('ordem')
    if 'ativo' in d:
        if not isinstance(d['ativo'], bool):
            return _erro('ativo inválido.')
        if d['ativo'] and not p.ativo:
            e = _limite_profissionais(loja, excluir=p.pk)
            if e:
                return _erro(e)
        if not d['ativo'] and p.ativo and _futuras(p).exists():
            return _erro('Este profissional tem marcações futuras — reatribui-as ou cancela-as primeiro.',
                         status.HTTP_409_CONFLICT, marcacoes=_lista_curta(_futuras(p)))
        p.ativo = d['ativo']
        campos.append('ativo')
    if campos:
        p.save(update_fields=campos)
    if 'servicos' in d:
        ids = d.get('servicos')
        if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
            return _erro('Lista de serviços inválida.')
        p.servicos.set(Servico.objects.filter(loja=loja, id__in=ids))
    return Response(profissional_payload(p, request))


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated])
def profissional_foto(request, loja_id, prof_id):
    """POST (multipart: ficheiro) / DELETE /app/loja/<id>/servicos/profissionais/<pid>/foto/"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    p = get_object_or_404(Profissional, id=prof_id, loja=loja)
    antigo = p.foto.name if p.foto else ''
    if request.method == 'DELETE':
        p.foto = None
    else:
        f = request.FILES.get('ficheiro')
        if not f:
            return _erro('Escolhe uma imagem.')
        from django.core.exceptions import ValidationError
        try:
            validar_ficheiro(Profissional._meta.get_field('foto'), f)
        except ValidationError as e:
            return _erro(e.messages[0])
        p.foto = f
    with transaction.atomic():
        p.save(update_fields=['foto'])
        if antigo:
            limpeza.agendar_apagar_depois_do_commit([antigo], 'substituido:profissional')
    return Response(profissional_payload(p, request))


def _hhmm(v):
    if not isinstance(v, str) or len(v) != 5:
        return None
    try:
        return time.fromisoformat(v)
    except ValueError:
        return None


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def profissional_horario(request, loja_id, prof_id):
    """
    PUT /app/loja/<id>/servicos/profissionais/<pid>/horario/ { blocos: [{dia_semana, inicio "HH:MM", fim "HH:MM"}] }
    Lista vazia = segue o horário da loja. Devolve as marcações futuras que ficam fora do horário (aviso).
    """
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    p = get_object_or_404(Profissional, id=prof_id, loja=loja)
    blocos = request.data.get('blocos')
    if not isinstance(blocos, list) or len(blocos) > 42:
        return _erro('Horário inválido.')
    limpos = []
    for b in blocos:
        if not isinstance(b, dict):
            return _erro('Horário inválido.')
        dia = _inteiro(b.get('dia_semana'), 0, 6)
        ini, fim = _hhmm(b.get('inicio')), _hhmm(b.get('fim'))
        if dia is None or ini is None or fim is None:
            return _erro('Cada bloco precisa do dia e das horas (HH:MM).')
        if fim <= ini:
            return _erro('A hora de fim tem de ser depois da de início.')
        limpos.append((dia, ini, fim))
    limpos.sort()
    for (d1, i1, f1), (d2, i2, f2) in zip(limpos, limpos[1:]):
        if d1 == d2 and i2 < f1:
            return _erro('Há blocos sobrepostos no mesmo dia.')
    with transaction.atomic():
        p.horarios.all().delete()
        HorarioProfissional.objects.bulk_create([HorarioProfissional(profissional=p, dia_semana=d, inicio=i, fim=f)
                                                 for d, i, f in limpos])
    p = Profissional.objects.prefetch_related('horarios', 'servicos').select_related('loja').get(pk=p.pk)
    fora = []
    for m in _futuras(p).select_related('profissional', 'cliente__user')[:200]:
        try:
            agenda.verificar(p, m.inicio, m.ocupado_ate, excluir=m.pk)
        except agenda.Indisponivel:
            fora.append(marcacao_payload(m))
    return Response({**profissional_payload(p, request), 'fora_do_horario': fora})


def ausencia_payload(a):
    tz = fuso()
    return {'id': a.id, 'inicio': a.inicio.astimezone(tz).isoformat(), 'fim': a.fim.astimezone(tz).isoformat(),
            'motivo': a.motivo, 'criada_por': a.criada_por}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ausencias(request, loja_id, prof_id):
    """
    GET  /app/loja/<id>/servicos/profissionais/<pid>/ausencias/   (as de hoje em diante)
    POST { inicio, fim (ISO) | de, ate (dias, inclusive), motivo } → devolve as marcações afectadas
    """
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes' if request.method == 'GET' else 'gerir_servicos')
    if erro:
        return erro
    p = get_object_or_404(Profissional, id=prof_id, loja=loja)
    if request.method == 'GET':
        return Response([ausencia_payload(a) for a in p.ausencias.filter(fim__gt=_agora())])
    d = request.data
    if d.get('de') is not None:
        de, ate = _ler_dia(d.get('de')), _ler_dia(d.get('ate') or d.get('de'))
        if not de or not ate or ate < de:
            return _erro('Datas inválidas.')
        tz = fuso()
        inicio, fim = datetime.combine(de, time(0), tzinfo=tz), datetime.combine(ate + timedelta(days=1), time(0), tzinfo=tz)
    else:
        inicio, fim = _ler_dt(d.get('inicio')), _ler_dt(d.get('fim'))
        if not inicio or not fim or fim <= inicio:
            return _erro('Indica o início e o fim (o fim depois do início).')
    if fim - inicio > timedelta(days=366):
        return _erro('Uma ausência pode ter no máximo um ano.')
    motivo, e = _texto(d, 'motivo', 200)
    if e:
        return _erro(e)
    a = AusenciaProfissional.objects.create(profissional=p, inicio=inicio, fim=fim, motivo=motivo, criada_por=_quem(membro))
    afetadas = Marcacao.objects.filter(profissional=p, estado__in=Marcacao.ATIVOS, inicio__lt=fim, ocupado_ate__gt=inicio)
    return Response({**ausencia_payload(a), 'afetadas': _lista_curta(afetadas)}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def ausencia_apagar(request, loja_id, ausencia_id):
    """DELETE /app/loja/<id>/servicos/ausencias/<aid>/"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_servicos')
    if erro:
        return erro
    get_object_or_404(AusenciaProfissional, id=ausencia_id, profissional__loja=loja).delete()
    return Response({'apagado': True})


# ══════════════════════════════════════════════════════════════
# AGENDA E MARCAÇÕES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agenda_ver(request, loja_id):
    """
    GET /app/loja/<id>/servicos/agenda/?inicio=AAAA-MM-DD&dias=1..14&profissional=<id>
    Por profissional: os blocos de trabalho de cada dia, as ausências e as marcações (todas, menos expiradas).
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _get_membro(request, loja)
    if not membro:
        return _erro('Sem permissão.', status.HTTP_403_FORBIDDEN)
    profs = loja.profissionais.prefetch_related('horarios').select_related('loja')
    if not membro.pode('gerir_marcacoes'):
        proprio = getattr(membro, 'profissional', None)
        if not proprio:
            return _erro('Sem permissão: gerir_marcacoes', status.HTTP_403_FORBIDDEN)
        profs = profs.filter(pk=proprio.pk)
    inicio = _ler_dia(request.GET.get('inicio')) or agenda.agora_mais(0).astimezone(fuso()).date()
    dias = _inteiro(request.GET.get('dias') or '1', 1, 14)
    if dias is None:
        return _erro('dias: 1 a 14.')
    pid = request.GET.get('profissional')
    if pid:
        if not pid.isdigit():
            return _erro('profissional inválido.')
        profs = profs.filter(pk=int(pid))
    profs = list(profs.filter(Q(ativo=True) | Q(marcacoes__inicio__date__gte=inicio)).distinct())
    tz = fuso()
    de = datetime.combine(inicio, time(0), tzinfo=tz)
    ate = de + timedelta(days=dias)
    excecoes = list(loja.excecoes.all())
    marc = (Marcacao.objects.filter(profissional__in=profs, inicio__lt=ate, ocupado_ate__gt=de)
            .exclude(estado='expirada').select_related('profissional', 'cliente__user'))
    aus = AusenciaProfissional.objects.filter(profissional__in=profs, inicio__lt=ate, fim__gt=de)
    return Response({
        'inicio': inicio.isoformat(), 'dias': dias,
        'pode_gerir': membro.pode('gerir_marcacoes'),
        'profissionais': [{
            'id': p.id, 'nome': p.nome, 'ativo': p.ativo,
            'blocos': {(inicio + timedelta(days=i)).isoformat(): [[a.astimezone(tz).isoformat(), f.astimezone(tz).isoformat()]
                       for a, f in agenda.horario_do_dia(p, inicio + timedelta(days=i), tz, excecoes)]
                       for i in range(dias)},
        } for p in profs],
        'ausencias': [{**ausencia_payload(a), 'profissional_id': a.profissional_id} for a in aus],
        'marcacoes': [marcacao_payload(m) for m in marc],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def disponibilidade(request, loja_id):
    """GET /app/loja/<id>/servicos/disponibilidade/?servico=<id>&dia=AAAA-MM-DD&profissional=<id>&excluir=<mid>"""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes')
    if erro:
        return erro
    sid = request.GET.get('servico') or ''
    dia = _ler_dia(request.GET.get('dia'))
    if not sid.isdigit() or not dia:
        return _erro('Indica o serviço e o dia.')
    s = get_object_or_404(Servico, id=int(sid), loja=loja)
    profs = s.profissionais.filter(ativo=True).prefetch_related('horarios').select_related('loja')
    pid = request.GET.get('profissional')
    if pid:
        if not pid.isdigit():
            return _erro('profissional inválido.')
        profs = Profissional.objects.filter(loja=loja, ativo=True, pk=int(pid)).prefetch_related('horarios')
    excluir = request.GET.get('excluir')
    excluir = int(excluir) if excluir and excluir.isdigit() else None
    horas = agenda.horas_livres(s, dia, list(profs), desde=agenda.agora_mais(0), excluir=excluir)
    return Response({'dia': dia.isoformat(), 'horas': [{'inicio': h['inicio'].isoformat(), 'profissionais': h['profissionais']}
                                                       for h in horas]})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def marcacoes(request, loja_id):
    """
    GET  /app/loja/<id>/servicos/marcacoes/?estado=&de=&ate=&q=  (lista)
    POST { servico_id, profissional_id?, inicio, cliente_nome, cliente_telefone?, notas_internas?, preco?, ignorar_horario? }
         marcação manual (telefone / balcão): fica confirmada, paga no local.
    """
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes')
    if erro:
        return erro
    if request.method == 'GET':
        qs = Marcacao.objects.filter(loja=loja).select_related('profissional', 'cliente__user').order_by('-inicio')
        if request.GET.get('estado') in dict(Marcacao.ESTADOS):
            qs = qs.filter(estado=request.GET['estado'])
        de, ate = _ler_dia(request.GET.get('de')), _ler_dia(request.GET.get('ate'))
        if de:
            qs = qs.filter(inicio__date__gte=de)
        if ate:
            qs = qs.filter(inicio__date__lte=ate)
        q = (request.GET.get('q') or '').strip()[:60]
        if q:
            qs = qs.filter(Q(cliente_nome__icontains=q) | Q(cliente__user__first_name__icontains=q)
                           | Q(cliente_telefone__icontains=q) | Q(servico_nome__icontains=q))
        return Response([marcacao_payload(m) for m in qs[:300]])
    d = request.data
    sid = d.get('servico_id')
    if isinstance(sid, bool) or not isinstance(sid, int):
        return _erro('Escolhe o serviço.')
    s = Servico.objects.filter(loja=loja, id=sid).first()
    if not s:
        return _erro('Serviço inválido.')
    prof = None
    if d.get('profissional_id') not in (None, ''):
        pid = d.get('profissional_id')
        if isinstance(pid, bool) or not isinstance(pid, int):
            return _erro('Profissional inválido.')
        prof = Profissional.objects.filter(loja=loja, id=pid).select_related('loja').first()
        if not prof:
            return _erro('Profissional inválido.')
    inicio = _ler_dt(d.get('inicio'))
    if not inicio:
        return _erro('Indica o dia e a hora.')
    if inicio < agenda.agora_mais(-60 * 24):
        return _erro('Não se marcam serviços no passado.')
    nome, e = _texto(d, 'cliente_nome', 120, True, 'O nome do cliente')
    if e:
        return _erro(e)
    tel, e = _texto(d, 'cliente_telefone', 30)
    if e:
        return _erro(e)
    notas, e = _texto(d, 'notas_internas', 500)
    if e:
        return _erro(e)
    preco = None
    if d.get('preco') not in (None, ''):
        preco, e = ler_valor(d.get('preco'), 'O preço')
        if e:
            return _erro(e)
    ign = d.get('ignorar_horario', False)
    if not isinstance(ign, bool):
        return _erro('ignorar_horario inválido.')
    try:
        m = ops.criar(loja, s, inicio, prof, cliente_nome=nome, cliente_telefone=tel, notas_internas=notas,
                      preco=preco, ignorar_horario=ign, por=_quem(membro))
    except ErroMarcacao as e:
        return _erro(str(e))
    if m.profissional.membro_id and m.profissional.membro.utilizador_id != membro.utilizador_id and m.profissional.membro.ativo:
        from ..Views.notificacaoView import notificar
        notificar(utilizador=m.profissional.membro.utilizador, tipo='marcacao_nova', titulo='Nova marcação',
                  mensagem=f'{m.servico_nome} a {ops.quando_texto(m.inicio)} — {nome}.', loja=loja,
                  link=f'/loja/{loja.id}/backoffice?seccao=servicos')
    return Response(marcacao_payload(m, completo=True), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def marcacao_ver(request, loja_id, marcacao_id):
    """GET /app/loja/<id>/servicos/marcacoes/<mid>/ — com o histórico de reatribuições."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _get_membro(request, loja)
    m = get_object_or_404(Marcacao.objects.select_related('profissional', 'cliente__user'), id=marcacao_id, loja=loja)
    proprio = getattr(membro, 'profissional', None) if membro else None
    if not membro or not (membro.pode('gerir_marcacoes') or (proprio and proprio.pk == m.profissional_id)):
        return _erro('Sem permissão.', status.HTTP_403_FORBIDDEN)
    return Response(marcacao_payload(m, completo=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcacao_acao(request, loja_id, marcacao_id):
    """
    POST /app/loja/<id>/servicos/marcacoes/<mid>/acao/
      { acao: 'confirmar' }
      { acao: 'cancelar', motivo }
      { acao: 'remarcar', inicio, ignorar_horario? }
      { acao: 'reatribuir', profissional_id, motivo?, ignorar_horario? }
      { acao: 'notas', notas_internas }
    """
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes')
    if erro:
        return erro
    m = get_object_or_404(Marcacao, id=marcacao_id, loja=loja)
    d = request.data
    acao = d.get('acao')
    por = _quem(membro)
    ign = d.get('ignorar_horario', False)
    if not isinstance(ign, bool):
        return _erro('ignorar_horario inválido.')
    avisos = []
    try:
        if acao == 'confirmar':
            m = ops.confirmar(m, por)
        elif acao == 'cancelar':
            motivo, e = _texto(d, 'motivo', 200, True, 'O motivo')
            if e:
                return _erro(e)
            m = ops.cancelar(m, por, motivo)
        elif acao == 'remarcar':
            inicio = _ler_dt(d.get('inicio'))
            if not inicio:
                return _erro('Indica o dia e a hora novos.')
            if inicio < agenda.agora_mais(-60 * 24):
                return _erro('Não se marcam serviços no passado.')
            motivo, e = _texto(d, 'motivo', 200)
            if e:
                return _erro(e)
            m = ops.remarcar(m, inicio, por, motivo, ign)
        elif acao == 'reatribuir':
            pid = d.get('profissional_id')
            if isinstance(pid, bool) or not isinstance(pid, int):
                return _erro('Escolhe o profissional.')
            novo = Profissional.objects.filter(loja=loja, id=pid).first()
            if not novo:
                return _erro('Profissional inválido.')
            motivo, e = _texto(d, 'motivo', 200)
            if e:
                return _erro(e)
            m, avisos = ops.reatribuir(m, novo, por, motivo, ign)
        elif acao == 'notas':
            notas, e = _texto(d, 'notas_internas', 500)
            if e:
                return _erro(e)
            m.notas_internas = notas
            m.save(update_fields=['notas_internas', 'data_atualizacao'])
        else:
            return _erro('Acção inválida.')
    except ErroMarcacao as e:
        return _erro(str(e))
    m = Marcacao.objects.select_related('profissional', 'cliente__user').get(pk=m.pk)
    return Response({**marcacao_payload(m, completo=True), 'avisos': avisos})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def livres_para_reatribuir(request, loja_id, marcacao_id):
    """GET /app/loja/<id>/servicos/marcacoes/<mid>/livres/ — os outros profissionais e se estão livres a essa hora."""
    loja, membro, erro = _acesso(request, loja_id, 'gerir_marcacoes')
    if erro:
        return erro
    m = get_object_or_404(Marcacao, id=marcacao_id, loja=loja)
    faz = set(m.servico.profissionais.values_list('id', flat=True))
    out = []
    for p in loja.profissionais.filter(ativo=True).exclude(pk=m.profissional_id).prefetch_related('horarios').select_related('loja'):
        livre, razao = True, ''
        try:
            agenda.verificar(p, m.inicio, m.ocupado_ate)
        except agenda.Indisponivel as e:
            livre, razao = False, str(e)
        out.append({'id': p.id, 'nome': p.nome, 'livre': livre, 'razao': razao, 'faz_o_servico': p.id in faz})
    out.sort(key=lambda x: (not x['livre'], not x['faz_o_servico'], x['nome']))
    return Response(out)
