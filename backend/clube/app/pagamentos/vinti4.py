"""
vinti4 / SISP — Pagamento Web com 3DS Server 2.2 (MOP021 v14, Protocolo de Segurança v2.0, Plan Test MOP022 v09).

Percurso:
  1. iniciar(): grava uma TransacaoVinti4 (ref curto = merchantRef) e devolve o formulário que o browser envia
     sozinho (POST, nunca num iframe) para a página da SISP, com o FingerPrint e os dados 3DS (purchaseRequest);
  2. a SISP manda o cliente de volta com um POST para /app/pagamento/vinti4/resposta/ (Views/vinti4View.py):
     processar_resposta() valida o resultFingerPrint com a chave certa e, se foi pago, chama servico.confirmar
     (encomenda/marcação/fatura/comissões pagas) — antes de o cliente voltar ao site;
  3. o cliente cai em /pagamento/callback?fornecedor=vinti4&ref=… e o frontend pergunta o resultado
     (confirmar_regresso, que só lê o que já ficou gravado);
  4. sem resposta em 8 minutos (o cliente fechou a página, a rede falhou): o worker pergunta à API de estado
     (rever_sem_resposta) — paga → como em 2; não paga → expirada; sem resposta da API → por confirmar.

Credenciais: sem loja = as da Bendi (settings.VINTI4_*: comissões e subscrições); com loja = as da AdesaoVinti4
dela (o contrato proíbe receber por conta de terceiros — cl. 4.ª n.º 2). A chave (posAutCode) nunca sai do
servidor nem vai para os registos.

Reembolsos: no Portal do Comerciante da SISP (a API de estorno é opcional); reembolsar() diz isso.
"""
import base64
import hashlib
import hmac
import logging
import re
import secrets
import string
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .base import Confirmacao, ErroPagamento, Fornecedor, Inicio

log = logging.getLogger(__name__)

MOEDA_CVE = '132'               # ISO 4217 numérico — a SISP só aceita escudos
COMPRA = '1'                    # transactionCode
SUCESSO_COMPRA = '8'            # messageType de uma compra paga (com merchantResp 'C')
ERRO = '6'
TEMPO_LIMITE = timedelta(minutes=8)          # MOP021 2.2.2.3 / Plan Test 38
CONSULTAS_MAX = 12                           # por_confirmar: tenta a API de 10 em 10 minutos durante 2 horas
INTERVALO_CONSULTAS = timedelta(minutes=10)
_ALFANUM = string.ascii_uppercase + string.digits


# ── FingerPrint (Pagamento Web — Especificação do Protocolo de Segurança) ──────────────────────

def _sha512_b64(texto):
    return base64.b64encode(hashlib.sha512(texto.encode('utf-8')).digest()).decode()


def _txt(v):
    """'Deve ser concatenado eliminando todos os espaços no início e no fim.'"""
    return str(v if v is not None else '').strip()


def _sem_espacos(v):
    """'Deve ser formatado de forma a eliminar todos os espaços em branco.'"""
    return ''.join(str(v if v is not None else '').split())


def _long(v):
    """Campos numéricos sem zeros à esquerda ('0000100' → '100'); vazio fica vazio."""
    v = _sem_espacos(v)
    return str(int(v)) if v.isdigit() else v


def _milesimos(valor):
    """Montante × 1000, só a parte inteira ('1000.00' → '1000000')."""
    try:
        return str(int(Decimal(_sem_espacos(valor) or '0') * 1000))
    except InvalidOperation:
        return ''


def fingerprint_pedido(chave, timestamp, montante, ref, sessao, pos_id,
                       moeda=MOEDA_CVE, codigo=COMPRA, entidade='', referencia_servico=''):
    return _sha512_b64(
        _sha512_b64(chave) + timestamp + _milesimos(montante) + _sem_espacos(ref) + _sem_espacos(sessao)
        + _sem_espacos(pos_id) + _long(moeda) + _sem_espacos(codigo) + _long(entidade) + _long(referencia_servico))


def fingerprint_sucesso(chave, d):
    """resultFingerPrint de uma resposta de sucesso (messageType 8, 10, P, M). `d`: o POST da SISP.
    Referência e entidade vão por esta ordem (a dos exemplos PHP/Node/Java da SISP; numa compra vêm vazias)."""
    g = lambda k: d.get(k, '')                                  # noqa: E731
    return _sha512_b64(
        _sha512_b64(chave) + _txt(g('messageType')) + _long(g('merchantRespCP')) + _long(g('merchantRespTid'))
        + _txt(g('merchantRespMerchantRef')) + _txt(g('merchantRespMerchantSession'))
        + _milesimos(g('merchantRespPurchaseAmount')) + _txt(g('merchantRespMessageID')) + _txt(g('merchantRespPan'))
        + _txt(g('merchantResp')) + _txt(g('merchantRespTimeStamp')) + _long(g('merchantRespReferenceNumber'))
        + _long(g('merchantRespEntityCode')) + _txt(g('merchantRespClientReceipt'))
        + _txt(g('merchantRespAdditionalErrorMessage')) + _txt(g('merchantRespReloadCode')))


def fingerprint_erro(chave, d):
    """resultFingerPrint de uma resposta de erro (messageType 6)."""
    g = lambda k: d.get(k, '')                                  # noqa: E731
    return _sha512_b64(
        _sha512_b64(chave) + _txt(g('messageType')) + _txt(g('merchantRespMessageID'))
        + _sem_espacos(g('merchantRespErrorCode')) + _txt(g('merchantRespErrorDetail'))
        + _txt(g('merchantRespErrorDescription')) + _txt(g('merchantRespMerchantRef'))
        + _txt(g('merchantRespMerchantSession')) + _txt(g('merchantRespAdditionalErrorMessage'))
        + _txt(g('merchantRespTimeStamp')))


def _igual(a, b):
    return bool(a) and bool(b) and hmac.compare_digest(str(a).strip(), str(b).strip())


# ── credenciais ─────────────────────────────────────────────────

@dataclass
class Credenciais:
    pos_id: str
    chave: str


def credenciais(loja=None, so_ativas=True):
    """Sem loja: as da Bendi. Com loja: as da adesão dela (ativa; em testes também, para o dono experimentar).
    so_ativas=False: para validar uma resposta de uma transacção já feita, mesmo que a adesão entretanto mude."""
    if loja is None:
        pos_id, chave = settings.VINTI4_POS_ID.strip(), settings.VINTI4_POS_AUT_CODE.strip()
    else:
        from ..utils import vinti4 as adesoes
        a = adesoes.adesao(loja)
        if not a or (so_ativas and a.estado not in ('teste', 'ativa')):
            raise ErroPagamento('Esta loja ainda não aceita cartão.')
        pos_id, chave = a.pos_id.strip(), adesoes.decifrar(a.chave_cifrada)
    if not (pos_id and chave):
        raise ErroPagamento('O pagamento com cartão está indisponível de momento.')
    return Credenciais(pos_id, chave)


def _credenciais_da(tx):
    if tx.loja_id is None:
        return credenciais(None)
    return credenciais(tx.loja, so_ativas=False)


# ── dados 3DS (purchaseRequest) ────────────────────────────────

def _yyyymmdd(dt):
    return timezone.localtime(dt).strftime('%Y%m%d') if dt else ''


def _indicador_idade(dt):
    """chAccAgeInd / chAccPwChangeInd: 03 menos de 30 dias, 04 entre 30 e 60, 05 mais de 60.
    '01 sem conta' não se usa (MD044 FAQ 12): para pagar com cartão é preciso conta."""
    dias = (timezone.now() - dt).days if dt else 0
    return '03' if dias < 30 else '04' if dias <= 60 else '05'


def _telefone(telefone, indicativo):
    """'+238 991 12 23' → {'cc': '238', 'subscriber': '9911223'} | None."""
    digitos = re.sub(r'\D', '', str(telefone or ''))
    if digitos.startswith('00'):
        digitos = digitos[2:]
    if not digitos:
        return None
    cc = indicativo or '238'
    if digitos.startswith(cc) and len(digitos) > len(cc) + 6:
        digitos = digitos[len(cc):]
    return {'cc': cc[:3], 'subscriber': digitos[:15]}


def dados_3ds(utilizador, morada=''):
    """Os parâmetros adicionais 3DS Server do pagador (Utilizador) — MOP021 2.2.1 e FAQ MD044."""
    from ..utils import geografia
    user = utilizador.user
    pais = geografia.pais(utilizador.pais) or geografia.pais('CV')
    concelho = geografia.concelho(utilizador.concelho) if pais[0] == 'CV' else None
    cidade = (utilizador.cidade or '').strip() or (concelho[1] if concelho else '')
    morada = ' '.join(str(morada or utilizador.morada or '').split())
    linha1 = morada[:50]
    d = {
        'acctID': str(user.pk),
        'acctInfo': {
            'chAccAgeInd': _indicador_idade(user.date_joined),
            'chAccDate': _yyyymmdd(user.date_joined),
            'chAccChange': _yyyymmdd(utilizador.data_atualizacao or user.date_joined),
            'chAccPwChange': _yyyymmdd(utilizador.password_alterada_em or user.date_joined),
            'chAccPwChangeInd': _indicador_idade(utilizador.password_alterada_em or user.date_joined),
            'suspiciousAccActivity': '01',
        },
        'email': user.email or '',
        'addrMatch': 'N',
        'billAddrCountry': pais[1],
        'billAddrCity': cidade[:50],
        'billAddrLine1': linha1,
        # só uma linha de morada: a 2.ª repete a 1.ª (FAQ 20)
        'billAddrLine2': morada[50:100] or linha1,
        'billAddrPostCode': (utilizador.codigo_postal or '').strip()[:16] or '0000',
    }
    if concelho:
        d['billAddrState'] = concelho[0]
    telefone = _telefone(utilizador.telefone, pais[2])
    if telefone:
        d['mobilePhone'] = telefone
    return d


def _codificar(dados):
    import json
    return base64.b64encode(json.dumps(dados, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).decode()


# ── pedido ──────────────────────────────────────────────────────

def montante(valor):
    """Escudos inteiros (a SISP recusa casas decimais)."""
    return int(Decimal(str(valor)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _novo(prefixo):
    return prefixo + ''.join(secrets.choice(_ALFANUM) for _ in range(14))


def url_resposta():
    return f'{settings.API_BASE_URL.rstrip("/")}/app/pagamento/vinti4/resposta/'


def _timestamp():
    return timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')


# ── resposta ────────────────────────────────────────────────────

MAX_RESPOSTAS = 10

# BT202108A 1.1 — erros do lado do comerciante (configuração, FingerPrint, parâmetros): o cliente não pode fazer
# nada; vê uma mensagem simples e a Bendi é avisada. Os de 1.2 (saldo, cartão, OTP…) mostram-se tal como vêm.
ERROS_COMERCIANTE = (
    'dados do pedido invalidos', 'invalid order data', 'donnees de commande invalides',
    'erro de formatacao', 'formatting error', 'erreur de formatage',
    'falha na configuracao', 'setup failed', "echec de l'installation",
    'data invalida', 'invalid date', 'date invalide',
    'dados invalido para este contexto', 'invalid data for this context', 'donnees invalides pour ce contexte',
    'falha nas chaves de autenticacao', 'authentication keys failed', "echec des cles d'authentification",
    'valor da transacao abaixo do minimo', 'transaction amount below the minimum', 'montant de la transaction inferieur',
)
MENSAGEM_ERRO_COMERCIANTE = ('Não foi possível concluir o pagamento por um problema do nosso lado. '
                             'Já fomos avisados — tenta de novo mais tarde.')


def _normalizar(texto):
    import unicodedata
    t = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(t.split())


def erro_do_comerciante(mensagem):
    m = _normalizar(mensagem)
    return bool(m) and any(e in m for e in ERROS_COMERCIANTE)


def _guardar_resposta(tx, origem, campos):
    """Junta o que a SISP mandou a tx.respostas (texto curto por campo, as últimas MAX_RESPOSTAS)."""
    limpos = {str(k)[:60]: (v if isinstance(v, (bool, int, float)) or v is None else str(v)[:400])
              for k, v in list((campos or {}).items())[:60]}
    tx.respostas = (list(tx.respostas or []) + [{'em': timezone.now().isoformat(timespec='seconds'),
                                                  'origem': origem, 'campos': limpos}])[-MAX_RESPOSTAS:]


def _cancelou(d):
    return _txt(d.get('userCancelled') or d.get('UserCancelled')).lower() == 'true'


def _avisar_admins(titulo, mensagem, loja=None):
    from ..models import Notificacao
    from ..Views.notificacaoView import notificar_admins
    if Notificacao.objects.filter(tipo='pagamento_reembolsar', titulo=titulo).exists():
        return
    notificar_admins(tipo='pagamento_reembolsar', titulo=titulo, mensagem=mensagem, loja=loja, link='/admin', email=2)


def _avisar_erro_comerciante(tx):
    """Erro de configuração/pedido do lado da Bendi (BT202108A 1.1): um aviso por hora, com o que a SISP disse."""
    from datetime import timedelta
    from ..models import Notificacao
    from ..Views.notificacaoView import notificar_admins
    if Notificacao.objects.filter(tipo='pagamento_erro', data_criacao__gte=timezone.now() - timedelta(hours=1)).exists():
        return
    notificar_admins(tipo='pagamento_erro', titulo=f'vinti4: erro de configuração — {tx.ref}',
                     mensagem=f'A SISP recusou o pedido {tx.ref} ({tx.referencia}): {tx.erro[13:200]}. '
                              f'Verifica o POS ID, o posAutCode e os parâmetros (Admin → Pagamentos → Cartão).',
                     loja=tx.loja, link='/admin/pagamentos', email=2)


def _registar(tx, evento, estado_anterior=''):
    from ..utils.registo import registar
    registar('vinti4', evento, objeto_id=tx.id, loja_id=tx.loja_id, valor=tx.valor, metodo='vinti4',
             estado_anterior=estado_anterior, estado_novo=tx.estado, referencia=tx.referencia,
             dados={'ref': tx.ref, 'transacao': tx.transacao, 'pan': tx.pan, 'confirmada_por': tx.confirmada_por,
                    'erro': tx.erro[:120]})


def _aplicar(tx, valor_pago=None):
    """A transacção ficou paga: a encomenda/marcação/fatura/cobrança passa a paga (servico.confirmar).
    Se já não puder ser aceite, servico.confirmar avisa a Bendi para reembolsar (efeito 'reembolso')."""
    from . import servico
    from ..utils.dinheiro import moeda_cobranca
    conf = Confirmacao(sucesso=True, referencia=tx.referencia, transacao=tx.transacao,
                       valor=tx.valor if valor_pago is None else valor_pago, moeda=moeda_cobranca('vinti4'))
    try:
        tx.efeito = servico.confirmar(FORNECEDOR, conf)['estado']
    except ErroPagamento as e:
        tx.efeito, tx.erro = 'erro', f'Pago mas não aplicado: {e}'[:300]
        _avisar_admins(f'Pagamento vinti4 por resolver — {tx.ref}',
                       f'A SISP confirmou {tx.montante} CVE ({tx.transacao}, {tx.referencia}) mas não foi possível '
                       f'dar o pagamento como feito: {e}. Verifica e, se for o caso, reembolsa no Portal do Comerciante.',
                       loja=tx.loja)
    tx.save(update_fields=['efeito', 'erro'])


def processar_resposta(d):
    """
    POST da SISP (dict) → TransacaoVinti4 (ou None se o merchantRef não é nosso). Só muda o estado com o
    resultFingerPrint certo; uma resposta de sucesso válida vale sempre (mesmo depois de cancelada/expirada:
    o dinheiro foi cobrado). Cancelar não leva FingerPrint — só fecha uma transacção ainda em aberto.
    """
    from ..models import TransacaoVinti4
    ref = _txt(d.get('merchantRespMerchantRef') or d.get('merchantRef'))
    with transaction.atomic():
        tx = TransacaoVinti4.objects.select_for_update(of=('self',)).select_related('loja').filter(ref=ref).first() if ref else None
        if not tx:
            log.warning('vinti4: resposta para um merchantRef desconhecido (%r)', ref[:20])
            return None
        anterior = tx.estado
        _guardar_resposta(tx, 'resposta', d)
        tx.save(update_fields=['respostas'])
        tipo = _txt(d.get('messageType'))
        if tipo == SUCESSO_COMPRA:
            chave = _credenciais_da(tx).chave
            if not _igual(d.get('resultFingerPrint'), fingerprint_sucesso(chave, d)):
                log.warning('vinti4: resultFingerPrint inválido na resposta de sucesso de %s', tx.ref)
                _registar(tx, 'cartao_assinatura_invalida', anterior)
                return tx
            if tx.estado == 'paga':                     # a mesma resposta outra vez
                return tx
            tx.message_type = tipo
            tx.periodo = _long(d.get('merchantRespCP'))[:10]
            tx.tid = _long(d.get('merchantRespTid'))[:10]
            tx.message_id = _txt(d.get('merchantRespMessageID'))[:20]
            tx.pan = _txt(d.get('merchantRespPan'))[:21]
            tx.dcc = {k: _txt(d.get(k)) for k in ('dcc', 'dccAmount', 'dccCurrency', 'dccMarkup', 'dccRate')
                      if _txt(d.get(k))} if _txt(d.get('dcc')).upper() == 'Y' else {}
            if _txt(d.get('merchantResp')) != 'C':
                tx.estado, tx.erro = 'falhada', f'merchantResp {_txt(d.get("merchantResp"))[:5]!r} com messageType 8'
                tx.mensagem = 'O pagamento não foi aprovado.'
                tx.terminada_em = timezone.now()
                tx.save()
                _registar(tx, 'cartao_recusado', anterior)
                return tx
            tx.estado, tx.confirmada_por, tx.terminada_em = 'paga', 'resposta', timezone.now()
            tx.save()
            _registar(tx, 'cartao_pago', anterior)
            pago = _milesimos(d.get('merchantRespPurchaseAmount'))
            valor_pago = None if pago == str(tx.montante * 1000) else Decimal(pago or '0') / 1000
            _aplicar(tx, valor_pago)
            return tx
        if tipo == ERRO:
            chave = _credenciais_da(tx).chave
            if not _igual(d.get('resultFingerPrint'), fingerprint_erro(chave, d)):
                log.warning('vinti4: resultFingerPrint inválido na resposta de erro de %s', tx.ref)
                return tx
            if tx.estado == 'paga':
                return tx
            tx.message_type, tx.estado, tx.terminada_em = tipo, 'falhada', timezone.now()
            tx.message_id = _txt(d.get('merchantRespMessageID'))[:20]
            tx.erro_codigo = _sem_espacos(d.get('merchantRespErrorCode'))[:2]
            tx.erro = ' — '.join(filter(None, (_txt(d.get('merchantRespErrorDescription')),
                                               _txt(d.get('merchantRespErrorDetail')))))[:300]
            tx.mensagem = _txt(d.get('merchantRespAdditionalErrorMessage'))[:200]
            do_comerciante = erro_do_comerciante(tx.mensagem) or erro_do_comerciante(tx.erro)
            if do_comerciante:
                tx.erro = f'[comerciante] {tx.mensagem} — {tx.erro}'[:300]
                tx.mensagem = MENSAGEM_ERRO_COMERCIANTE
            tx.save()
            _registar(tx, 'cartao_recusado', anterior)
            if do_comerciante:
                _avisar_erro_comerciante(tx)
            return tx
        if _cancelou(d):
            if tx.estado in ('iniciada', 'por_confirmar'):
                tx.estado, tx.terminada_em = 'cancelada', timezone.now()
                tx.save(update_fields=['estado', 'terminada_em'])
                _registar(tx, 'cartao_cancelado', anterior)
            return tx
        log.warning('vinti4: resposta sem messageType nem cancelamento para %s', tx.ref)
        return tx


# ── API de estado (Plan Test 38–41) ────────────────────────────

def consultar_estado(tx):
    """Pergunta à SISP se a transacção foi paga → 'paga' | 'nao_paga' | None (sem API, sem resposta ou recusada)."""
    return consultar(tx)[0]


def consultar(tx):
    """→ (resultado, corpo da resposta da API ou None). Só para as transacções da Bendi: as das lojas pedem o
    portal de cada uma (fase das lojas)."""
    portal, password = settings.VINTI4_PORTAL_ID.strip(), settings.VINTI4_PORTAL_PASSWORD.strip()
    if tx.loja_id is not None or not (portal and password and settings.VINTI4_ESTADO_URL):
        return None, None
    try:
        cred = _credenciais_da(tx)
        resp = requests.post(settings.VINTI4_ESTADO_URL, auth=(portal, password), timeout=15,
                             json={'posID': cred.pos_id, 'posAuthCode': cred.chave, 'merchantRef': tx.ref})
        corpo = resp.json()
    except (ErroPagamento, requests.RequestException, ValueError) as e:
        log.warning('vinti4: API de estado sem resposta para %s: %s', tx.ref, type(e).__name__)
        return None, {'erro': type(e).__name__}
    if not isinstance(corpo, dict):
        return None, {'erro': 'resposta inesperada'}
    if corpo.get('result') is not True:
        log.warning('vinti4: API de estado recusou %s: %s', tx.ref, str(corpo.get('msg'))[:120])
        return None, corpo
    return ('paga' if corpo.get('transactionSuccess') is True else 'nao_paga'), corpo


def rever_sem_resposta(agora=None):
    """Worker, uma vez por minuto: as transacções sem resposta há mais de 8 minutos. → quantas mudaram."""
    from django.db.models import Q
    from ..models import TransacaoVinti4
    agora = agora or timezone.now()
    candidatas = TransacaoVinti4.objects.filter(
        Q(estado='iniciada', criada_em__lt=agora - TEMPO_LIMITE)
        | Q(estado='por_confirmar', consultas__lt=CONSULTAS_MAX, consultada_em__lt=agora - INTERVALO_CONSULTAS)
    ).values_list('id', flat=True)[:50]
    mudaram = 0
    for tid in list(candidatas):
        tx = TransacaoVinti4.objects.select_related('loja').get(pk=tid)
        resultado, corpo = consultar(tx)
        with transaction.atomic():
            tx = TransacaoVinti4.objects.select_for_update(of=('self',)).select_related('loja').get(pk=tid)
            if tx.estado not in ('iniciada', 'por_confirmar'):     # a resposta chegou entretanto
                continue
            anterior = tx.estado
            if corpo is not None:
                _guardar_resposta(tx, 'estado', corpo)
            tx.consultas += 1
            tx.consultada_em = agora
            if resultado == 'paga':
                tx.estado, tx.confirmada_por, tx.terminada_em = 'paga', 'estado', agora
            elif resultado == 'nao_paga':
                tx.estado, tx.terminada_em, tx.mensagem = 'expirada', agora, 'Sem resposta da SISP: o pagamento não foi feito.'
            else:
                tx.estado = 'por_confirmar'
            tx.save()
            if tx.estado != anterior:
                mudaram += 1
                _registar(tx, f'cartao_{tx.estado}', anterior)
            if tx.estado == 'paga':
                _aplicar(tx)
    return mudaram


# ── o fornecedor ────────────────────────────────────────────────

class Vinti4(Fornecedor):
    codigo = 'vinti4'
    nome = 'vinti4'

    def iniciar(self, cobranca):
        from ..models import TransacaoVinti4
        pagador = cobranca.pagador
        if pagador is None:
            raise ErroPagamento('Para pagar com cartão é preciso ter sessão iniciada.')
        from .servico import exigir_dados_cliente
        exigir_dados_cliente(pagador, cobranca.morada)      # também nas faturas e comissões da Bendi (3DS)
        valor = Decimal(str(cobranca.valor))
        cobrar = montante(valor)
        if cobrar <= 1:                         # a SISP recusa valores iguais ou abaixo de 1$00
            raise ErroPagamento('O valor é demasiado baixo para pagar com cartão.')
        cred = credenciais(cobranca.loja)
        tx = TransacaoVinti4.objects.create(
            ref=_novo('B'), sessao=_novo('S'), referencia=cobranca.referencia[:80], loja=cobranca.loja,
            pos_id=cred.pos_id, utilizador=pagador.user, valor=valor, montante=cobrar,
            descricao=(cobranca.descricao or '')[:100])
        ts = _timestamp()
        fp = fingerprint_pedido(cred.chave, ts, cobrar, tx.ref, tx.sessao, cred.pos_id)
        campos = {
            'transactionCode': COMPRA, 'posID': cred.pos_id, 'merchantRef': tx.ref, 'merchantSession': tx.sessao,
            'amount': str(cobrar), 'currency': MOEDA_CVE, 'is3DSec': '1', 'urlMerchantResponse': url_resposta(),
            'languageMessages': 'pt', 'FingerPrint': fp, 'FingerPrintVersion': '1', 'TimeStamp': ts,
            'purchaseRequest': _codificar(dados_3ds(pagador, cobranca.morada)),
        }
        # os exemplos da SISP mandam também o FingerPrint no endereço; a especificação, no formulário — vão os dois
        url = f'{settings.VINTI4_URL}?{urlencode({"FingerPrint": fp, "TimeStamp": ts, "FingerPrintVersion": "1"})}'
        return Inicio('redirecionar', transacao=tx.transacao, url=url, metodo_http='POST', campos=campos)

    def confirmar_regresso(self, dados):
        """O cliente voltou da SISP (/pagamento/callback?fornecedor=vinti4&ref=…): só se lê o que
        processar_resposta já gravou — o que o browser traz nunca chega para dar nada como pago."""
        from ..models import TransacaoVinti4
        ref = _txt(dados.get('ref'))[:15]
        tx = TransacaoVinti4.objects.filter(ref=ref).first() if ref else None
        if not tx:
            raise ErroPagamento('Pagamento não encontrado.')
        if tx.estado == 'paga':
            if tx.efeito == 'erro':
                raise ErroPagamento('O pagamento foi recebido mas ainda não ficou registado. A equipa já foi avisada '
                                    'e resolve isto contigo.', destino_ref=tx.referencia)
            return Confirmacao(sucesso=True, referencia=tx.referencia, transacao=tx.transacao, valor=tx.valor,
                               moeda=_moeda())
        mensagens = {
            'cancelada': 'Pagamento cancelado.',
            'falhada': tx.mensagem or 'O pagamento não foi aprovado.',
            'iniciada': 'Ainda não temos a resposta da SISP. Se pagaste, a confirmação chega dentro de minutos.',
            'por_confirmar': 'Ainda não temos a confirmação da SISP. Se pagaste, avisamos-te quando chegar.',
            'expirada': 'O pagamento não foi concluído.',
        }
        raise ErroPagamento(mensagens.get(tx.estado, 'O pagamento não foi concluído.'), destino_ref=tx.referencia)

    def reembolsar(self, transacao, valor, chave=''):
        raise ErroPagamento('Os pagamentos com cartão vinti4 devolvem-se no Portal do Comerciante da SISP.')


def _moeda():
    from ..utils.dinheiro import moeda_cobranca
    return moeda_cobranca('vinti4')


FORNECEDOR = Vinti4()
