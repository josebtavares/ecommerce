"""
Registo das transações (models.RegistoTransacao) — prova em disputas e auditorias (SISP, banco, Finanças).

Regras:
- só se acrescenta: a base de dados recusa UPDATE/DELETE/TRUNCATE (migração 0073); uma correcção é uma linha nova;
- cada linha leva o hash da anterior (sha256) — verificar_cadeia() encontra qualquer linha mexida ou tirada;
- quem, de onde e em que pedido: o middleware guarda o pedido em curso (ator = utilizador autenticado;
  sem pedido = sistema: worker, prazos, comandos);
- nunca dados de cartão; em `dados`, NIB e números longos vão mascarados (só os 4 últimos).

O que se regista (ligar(), em AppConfig.ready()):
- Pagamento de encomenda: criado, mudança de estado, mudança de valor;
- Reembolso: pedido e cada mudança de estado;
- Marcação: paga online, reembolsada (marcacoes.reembolsar chama registar);
- Fatura de subscrição: emitida, paga, anulada (anulações em massa por anular_faturas);
- Dados bancários da loja: alterados, consultados pelo admin.
Fica na mesma transacção da mudança: se ela falhar, a linha também não fica.
"""
import contextvars
import hashlib
import json
import re
import uuid
from decimal import Decimal

from django.db import connection, transaction
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

_pedido = contextvars.ContextVar('registo_pedido', default=None)
_LOCK = 7307_0001          # pg_advisory_xact_lock: uma linha de cada vez (a cadeia não se parte)


# ── contexto do pedido ─────────────────────────────────────────

class RegistoPedidoMiddleware:
    """Guarda o pedido em curso para o registo saber quem, de onde e em que pedido (depois do IP real)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.pedido_id = (request.META.get('HTTP_X_RAILWAY_REQUEST_ID') or uuid.uuid4().hex)[:64]
        token = _pedido.set(request)
        try:
            return self.get_response(request)
        finally:
            _pedido.reset(token)


def _contexto():
    req = _pedido.get()
    if req is None:
        return None, '', ''
    user = getattr(req, 'user', None)       # o DRF põe aqui o utilizador do token depois de autenticar
    ator = user.pk if user is not None and getattr(user, 'is_authenticated', False) else None
    return ator, (req.META.get('REMOTE_ADDR') or '')[:45], getattr(req, 'pedido_id', '')


# ── mascarar ───────────────────────────────────────────────────

_PROIBIDAS = ('cartao', 'card', 'pan', 'cvv', 'cvc', 'validade', 'expiry', 'password', 'pin')
_NUMERO_LONGO = re.compile(r'\d[\d ]{10,}\d')


def mascarar(texto):
    """'000300004547069110176' → '•••• 0176' (qualquer sequência de 12+ dígitos)."""
    return _NUMERO_LONGO.sub(lambda m: '•••• ' + re.sub(r'\D', '', m.group())[-4:], str(texto))


def _limpar(dados):
    out = {}
    for k, v in (dados or {}).items():
        if any(p in str(k).lower() for p in _PROIBIDAS):
            continue
        out[str(k)] = mascarar(v) if v is not None else ''
    return out


# ── escrever ───────────────────────────────────────────────────

def _txt(v):
    return '' if v is None else str(v)


def _valor(v):
    return None if v is None else Decimal(v).quantize(Decimal('0.01'))


def calcular_hash(r):
    """Hash de uma linha (instância ou dict com os mesmos campos) — igual ao gravar e ao verificar."""
    g = r.get if isinstance(r, dict) else (lambda k: getattr(r, k))
    valor = g('valor')
    corpo = [
        g('hash_anterior'), g('criado_em').isoformat(), g('tipo'), g('evento'),
        _txt(g('objeto_id')), _txt(g('loja_id')), _txt(g('pos_id')), _txt(g('encomenda_id')),
        '' if valor is None else f'{Decimal(valor):.2f}',
        g('estado_anterior'), g('estado_novo'), g('metodo'), g('referencia'),
        _txt(g('ator_id')), g('ip'), g('pedido_id'), g('dados'),
    ]
    return hashlib.sha256(json.dumps(corpo, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def registar(tipo, evento, *, objeto_id=None, loja_id=None, pos_id=None, encomenda_id=None, valor=None,
             estado_anterior='', estado_novo='', metodo='', referencia='', dados=None):
    from ..models import RegistoTransacao
    ator, ip, pedido = _contexto()
    with transaction.atomic():
        if connection.vendor == 'postgresql':
            with connection.cursor() as c:
                c.execute('SELECT pg_advisory_xact_lock(%s)', [_LOCK])
        anterior = RegistoTransacao.objects.order_by('-id').values_list('hash', flat=True).first() or ''
        r = RegistoTransacao(
            criado_em=timezone.now(), tipo=tipo, evento=evento[:40], objeto_id=objeto_id, loja_id=loja_id,
            pos_id=pos_id, encomenda_id=encomenda_id, valor=_valor(valor),
            estado_anterior=_txt(estado_anterior)[:20], estado_novo=_txt(estado_novo)[:20],
            metodo=_txt(metodo)[:30], referencia=_txt(referencia)[:255],
            ator_id=ator, ip=ip, pedido_id=pedido, dados=_limpar(dados), hash_anterior=anterior,
        )
        r.hash = calcular_hash(r)
        r.save(force_insert=True)
    return r


def verificar_cadeia(lote=2000):
    """{total, ok, primeiro_erro: {id, motivo} | None} — percorre tudo por ordem."""
    from ..models import RegistoTransacao
    campos = ['id', 'criado_em', 'tipo', 'evento', 'objeto_id', 'loja_id', 'pos_id', 'encomenda_id', 'valor',
              'estado_anterior', 'estado_novo', 'metodo', 'referencia', 'ator_id', 'ip', 'pedido_id', 'dados',
              'hash_anterior', 'hash']
    anterior, total, ultimo_id = '', 0, 0
    while True:
        linhas = list(RegistoTransacao.objects.filter(id__gt=ultimo_id).order_by('id').values(*campos)[:lote])
        if not linhas:
            break
        for r in linhas:
            total += 1
            if r['hash_anterior'] != anterior:
                return {'total': total, 'ok': False, 'primeiro_erro': {'id': r['id'], 'motivo': 'falta uma linha antes desta ou foi alterada'}}
            if calcular_hash(r) != r['hash']:
                return {'total': total, 'ok': False, 'primeiro_erro': {'id': r['id'], 'motivo': 'o conteúdo não corresponde ao hash'}}
            anterior = r['hash']
            ultimo_id = r['id']
    return {'total': total, 'ok': True, 'primeiro_erro': None}


# ── anulações em massa (update() não passa pelos signals) ─────

def anular_faturas(qs, **campos):
    """qs.update(**campos) de faturas de subscrição, com uma linha no registo por fatura."""
    linhas = list(qs.values('id', 'loja_id', 'pos_id', 'valor', 'estado'))
    n = qs.update(**campos)
    for f in linhas:
        registar('subscricao', 'anulada', objeto_id=f['id'], loja_id=f['loja_id'], pos_id=f['pos_id'], valor=f['valor'],
                 estado_anterior=f['estado'], estado_novo=campos.get('estado', ''), dados={'notas': campos.get('notas', '')})
    return n


# ── signals ────────────────────────────────────────────────────
# pre_save lê o estado anterior na base (fonte de verdade: o objeto em memória pode estar desactualizado
# ou ter campos adiados); post_save escreve a linha. Só estes 4 modelos — gravam-se poucas vezes.

CAMPOS = {}     # modelo → campos a comparar (preenchido em ligar())


def _antes(sender, instance, raw=False, **kw):
    instance._registo = None
    if raw or not instance.pk:
        return
    instance._registo = sender.objects.filter(pk=instance.pk).values(*CAMPOS[sender]).first()


def _metodo_pagamento(p):
    m = getattr(p, 'metodo', None)
    return getattr(m, 'tipo', '') if m else ''


def _ao_gravar_pagamento(sender, instance, created, raw=False, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    base = dict(objeto_id=instance.pk, loja_id=instance.encomenda.loja_id, encomenda_id=instance.encomenda_id,
                valor=instance.valor, metodo=_metodo_pagamento(instance), referencia=instance.referencia_transacao)
    if created or antes is None:
        registar('encomenda', 'pagamento_criado', estado_novo=instance.status, **base)
        return
    if antes['status'] != instance.status:
        registar('encomenda', 'pagamento_' + instance.status, estado_anterior=antes['status'], estado_novo=instance.status, **base)
    if Decimal(antes['valor']) != Decimal(instance.valor):
        registar('encomenda', 'valor_alterado', estado_novo=instance.status,
                 dados={'valor_anterior': f"{Decimal(antes['valor']):.2f}"}, **base)


def _ao_gravar_reembolso(sender, instance, created, raw=False, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if created or antes is None or antes['estado'] != instance.estado:
        valor = instance.valor_aprovado if instance.valor_aprovado is not None else instance.valor_pedido
        registar('reembolso', 'pedido' if created else instance.estado, objeto_id=instance.pk, loja_id=instance.loja_id,
                 encomenda_id=instance.encomenda_id, valor=valor, estado_anterior=(antes or {}).get('estado', ''),
                 estado_novo=instance.estado, metodo=instance.metodo, referencia=instance.referencia,
                 dados={'tipo': instance.tipo, 'motivo': instance.motivo, 'origem': instance.origem})


def _ao_gravar_marcacao(sender, instance, created, raw=False, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if instance.pago and not (antes or {}).get('pago'):
        registar('marcacao', 'paga', objeto_id=instance.pk, loja_id=instance.loja_id, valor=instance.valor_pago,
                 estado_novo=instance.estado, metodo=instance.pagamento)


def _ao_gravar_fatura(sender, instance, created, raw=False, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if created or antes is None or antes['estado'] != instance.estado:
        registar('subscricao', 'emitida' if created else instance.estado, objeto_id=instance.pk,
                 loja_id=instance.loja_id, pos_id=instance.pos_id, valor=instance.valor,
                 estado_anterior=(antes or {}).get('estado', ''), estado_novo=instance.estado,
                 metodo=instance.metodo, referencia=instance.referencia,
                 dados={'descricao': instance.descricao, 'vencimento': instance.vencimento})


def ligar():
    """Chamado em AppConfig.ready()."""
    from ..models import FaturaSubscricao, Pagamento, Reembolso
    from ..servicos.models import Marcacao
    for modelo, campos, gravar in ((Pagamento, ('status', 'valor'), _ao_gravar_pagamento),
                                   (Reembolso, ('estado',), _ao_gravar_reembolso),
                                   (Marcacao, ('pago',), _ao_gravar_marcacao),
                                   (FaturaSubscricao, ('estado',), _ao_gravar_fatura)):
        CAMPOS[modelo] = campos
        nome = modelo.__name__
        pre_save.connect(_antes, sender=modelo, weak=False, dispatch_uid=f'registo_antes_{nome}')
        post_save.connect(gravar, sender=modelo, weak=False, dispatch_uid=f'registo_save_{nome}')
