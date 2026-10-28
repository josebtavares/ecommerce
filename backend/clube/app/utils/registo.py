"""
Registo das transações (models.RegistoTransacao) — prova em disputas e auditorias (SISP, banco, Finanças).

Regras:
- só se acrescenta: a base de dados recusa UPDATE/DELETE/TRUNCATE (migração 0073); uma correcção é uma linha nova;
- cada linha leva o hash do conteúdo; depois do commit selar() liga-a à cadeia (seq + hash da anterior, sha256)
  — verificar_cadeia() encontra qualquer linha mexida ou tirada;
- quem, de onde e em que pedido: o middleware guarda o pedido em curso (ator = utilizador autenticado;
  sem pedido = sistema: worker, prazos, comandos);
- nunca dados de cartão; em `dados`, NIB e números longos vão mascarados (só os 4 últimos).

O que se regista (ligar(), em AppConfig.ready()):
- Pagamento de encomenda: criado, mudança de estado, mudança de valor;
- Reembolso: pedido e cada mudança de estado;
- Marcação: paga online, reembolsada (marcacoes.reembolsar chama registar);
- Fatura de subscrição: emitida, paga, anulada (anulações em massa por anular_faturas);
- Dados bancários da loja: alterados, consultados pelo admin.
Fica na mesma transacção da mudança: se ela falhar, a linha também não fica (nem é selada).
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
_LOCK = 7307_0001          # pg_advisory_xact_lock de selar(): um elo de cada vez (a cadeia não se parte)


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

# chaves de `dados` que nunca se guardam (por palavra: 'pan' tira 'pan'/'card_pan', não 'empresa')
_PROIBIDAS = {'cartao', 'card', 'pan', 'cvv', 'cvc', 'cvv2', 'validade', 'expiry', 'password', 'pin', 'track'}
_NUMERO_LONGO = re.compile(r'\d[\d ]{10,}\d')


def mascarar(texto):
    """'000300004547069110176' → '•••• 0176' (qualquer sequência de 12+ dígitos)."""
    return _NUMERO_LONGO.sub(lambda m: '•••• ' + re.sub(r'\D', '', m.group())[-4:], str(texto))


def _limpar(dados):
    out = {}
    for k, v in (dados or {}).items():
        if _PROIBIDAS & set(re.split(r'[^a-z0-9]+', str(k).lower())):
            continue
        out[str(k)] = mascarar(v) if v is not None else ''
    return out


# ── escrever ───────────────────────────────────────────────────

def _txt(v):
    return '' if v is None else str(v)


def _valor(v):
    return None if v is None else Decimal(v).quantize(Decimal('0.01'))


CAMPOS_CONTEUDO = ['criado_em', 'tipo', 'evento', 'objeto_id', 'loja_id', 'pos_id', 'encomenda_id', 'valor',
                   'estado_anterior', 'estado_novo', 'metodo', 'referencia', 'ator_id', 'ip', 'pedido_id', 'dados']


def hash_conteudo(r):
    """Hash do conteúdo de uma linha (instância ou dict) — igual ao gravar e ao verificar."""
    g = r.get if isinstance(r, dict) else (lambda k: getattr(r, k))
    valor = g('valor')
    corpo = [
        g('criado_em').isoformat(), g('tipo'), g('evento'),
        _txt(g('objeto_id')), _txt(g('loja_id')), _txt(g('pos_id')), _txt(g('encomenda_id')),
        '' if valor is None else f'{Decimal(valor):.2f}',
        g('estado_anterior'), g('estado_novo'), g('metodo'), g('referencia'),
        _txt(g('ator_id')), g('ip'), g('pedido_id'), g('dados'),
    ]
    return hashlib.sha256(json.dumps(corpo, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def hash_elo(anterior, seq, conteudo):
    """Elo da cadeia: o hash anterior + a posição + o hash do conteúdo."""
    return hashlib.sha256(f'{anterior}|{seq}|{conteudo}'.encode()).hexdigest()


def registar(tipo, evento, *, objeto_id=None, loja_id=None, pos_id=None, encomenda_id=None, valor=None,
             estado_anterior='', estado_novo='', metodo='', referencia='', dados=None):
    """Escreve a linha já (na transacção de quem chama) com o hash do conteúdo; o elo da cadeia
    (seq, hash_anterior, hash) põe-se depois do commit, em selar() — numa transacção curta à parte.
    Assim nenhum pagamento espera por um bloqueio global (que, segurado até ao fim da transacção
    junto com os bloqueios de linhas de pagamentos/reembolsos, podia dar deadlock)."""
    from ..models import RegistoTransacao
    ator, ip, pedido = _contexto()
    r = RegistoTransacao(
        criado_em=timezone.now(), tipo=tipo, evento=evento[:40], objeto_id=objeto_id, loja_id=loja_id,
        pos_id=pos_id, encomenda_id=encomenda_id, valor=_valor(valor),
        estado_anterior=_txt(estado_anterior)[:20], estado_novo=_txt(estado_novo)[:20],
        metodo=_txt(metodo)[:30], referencia=_txt(referencia)[:255],
        ator_id=ator, ip=ip, pedido_id=pedido, dados=_limpar(dados),
    )
    r.hash_conteudo = hash_conteudo(r)
    r.save(force_insert=True)
    transaction.on_commit(_selar_seguro)
    return r


def selar(lote=500):
    """Liga à cadeia, por ordem de id, as linhas já gravadas que ainda não têm elo. Devolve quantas.
    Uma de cada vez em todo o sistema (pg_advisory_xact_lock) e em transacções curtas que só tocam
    no registo. O trigger só deixa preencher seq/hash_anterior/hash de uma linha que ainda não os tinha."""
    from ..models import RegistoTransacao
    total = 0
    while True:
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as c:
                    c.execute('SELECT pg_advisory_xact_lock(%s)', [_LOCK])
            ultimo = RegistoTransacao.objects.filter(seq__isnull=False).order_by('-seq').values('seq', 'hash').first()
            seq, anterior = (ultimo['seq'], ultimo['hash']) if ultimo else (0, '')
            linhas = list(RegistoTransacao.objects.filter(seq__isnull=True).order_by('id')
                          .values_list('id', 'hash_conteudo')[:lote])
            for pk, conteudo in linhas:
                seq += 1
                h = hash_elo(anterior, seq, conteudo)
                RegistoTransacao.objects.filter(pk=pk, seq__isnull=True).update(seq=seq, hash_anterior=anterior, hash=h)
                anterior = h
            total += len(linhas)
        if len(linhas) < lote:
            return total


def _selar_seguro():
    try:
        selar()
    except Exception:       # fica por selar; o próximo registo, a verificação ou o worker selam-na
        import logging
        logging.getLogger(__name__).exception('registo: selar falhou')


def verificar_cadeia(lote=2000):
    """{total, ok, por_selar, primeiro_erro: {id, motivo} | None} — sela o que faltar e percorre tudo pela ordem da cadeia."""
    from ..models import RegistoTransacao
    selar()
    campos = ['id', 'seq', 'hash_conteudo', 'hash_anterior', 'hash', *CAMPOS_CONTEUDO]
    anterior, total, ultimo_seq = '', 0, 0

    def erro(r, motivo):
        return {'total': total, 'ok': False, 'por_selar': por_selar, 'primeiro_erro': {'id': r['id'], 'motivo': motivo}}

    por_selar = RegistoTransacao.objects.filter(seq__isnull=True).count()
    while True:
        linhas = list(RegistoTransacao.objects.filter(seq__gt=ultimo_seq).order_by('seq').values(*campos)[:lote])
        if not linhas:
            break
        for r in linhas:
            total += 1
            if r['seq'] != ultimo_seq + 1:
                return erro(r, f'falta a linha n.º {ultimo_seq + 1} da cadeia (apagada?)')
            if r['hash_anterior'] != anterior:
                return erro(r, 'não aponta para a linha anterior')
            if hash_conteudo(r) != r['hash_conteudo']:
                return erro(r, 'o conteúdo foi alterado')
            if hash_elo(anterior, r['seq'], r['hash_conteudo']) != r['hash']:
                return erro(r, 'o elo da cadeia não bate certo')
            anterior, ultimo_seq = r['hash'], r['seq']
    return {'total': total, 'ok': True, 'por_selar': por_selar, 'primeiro_erro': None}


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


def _gravou(campo, update_fields):
    """save(update_fields=[...]) só grava esses campos — o resto em memória pode estar desactualizado."""
    return update_fields is None or campo in update_fields


def _metodo_pagamento(p):
    m = getattr(p, 'metodo', None)
    return getattr(m, 'tipo', '') if m else ''


def _ao_gravar_pagamento(sender, instance, created, raw=False, update_fields=None, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    base = dict(objeto_id=instance.pk, loja_id=instance.encomenda.loja_id, encomenda_id=instance.encomenda_id,
                valor=instance.valor, metodo=_metodo_pagamento(instance), referencia=instance.referencia_transacao)
    if created or antes is None:
        registar('encomenda', 'pagamento_criado', estado_novo=instance.status, **base)
        return
    if _gravou('status', update_fields) and antes['status'] != instance.status:
        registar('encomenda', 'pagamento_' + instance.status, estado_anterior=antes['status'], estado_novo=instance.status, **base)
    if _gravou('valor', update_fields) and Decimal(antes['valor']) != Decimal(instance.valor):
        registar('encomenda', 'valor_alterado', estado_novo=instance.status,
                 dados={'valor_anterior': f"{Decimal(antes['valor']):.2f}"}, **base)


def _ao_gravar_reembolso(sender, instance, created, raw=False, update_fields=None, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if created or antes is None or (_gravou('estado', update_fields) and antes['estado'] != instance.estado):
        valor = instance.valor_aprovado if instance.valor_aprovado is not None else instance.valor_pedido
        registar('reembolso', 'pedido' if created else instance.estado, objeto_id=instance.pk, loja_id=instance.loja_id,
                 encomenda_id=instance.encomenda_id, valor=valor, estado_anterior=(antes or {}).get('estado', ''),
                 estado_novo=instance.estado, metodo=instance.metodo, referencia=instance.referencia,
                 dados={'tipo': instance.tipo, 'motivo': instance.motivo, 'origem': instance.origem})


def _ao_gravar_marcacao(sender, instance, created, raw=False, update_fields=None, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if _gravou('pago', update_fields) and instance.pago and not (antes or {}).get('pago'):
        registar('marcacao', 'paga', objeto_id=instance.pk, loja_id=instance.loja_id, valor=instance.valor_pago,
                 estado_novo=instance.estado, metodo=instance.pagamento)


def _ao_gravar_fatura(sender, instance, created, raw=False, update_fields=None, **kw):
    if raw:
        return
    antes = getattr(instance, '_registo', None)
    if created or antes is None or (_gravou('estado', update_fields) and antes['estado'] != instance.estado):
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
