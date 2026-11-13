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
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import urlencode, urlsplit

import requests
from requests.adapters import HTTPAdapter
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
# depois das 12: continua a perguntar, devagar (o Portal pode ser indicado mais tarde, a API pode ter estado em baixo)
INTERVALO_LENTO = timedelta(hours=6)
PRAZO_CONSULTAS = timedelta(days=30)         # depois disto, só o "Perguntar à SISP" (à mão)
CAMPOS_SESSAO = ('merchantSession', 'merchantRespMerchantSession')     # segredo: não se mostra nas respostas guardadas
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


# ── ambiente (teste / produção) ─────────────────────────────────

def em_uso():
    """O vinti4 está ligado (vendas das lojas ou cobranças da Bendi)."""
    return 'vinti4' in (getattr(settings, 'PAGAMENTOS_FORNECEDOR', ''), getattr(settings, 'PAGAMENTOS_FORNECEDOR_BENDI', ''))


def ambiente():
    """'teste' se algum endereço da SISP é o do ambiente de teste (os valores por omissão), senão 'producao'."""
    urls = (settings.VINTI4_URL, settings.VINTI4_ESTADO_URL)
    return 'teste' if any('teste' in str(u or '').lower() for u in urls) else 'producao'


def verificar_configuracao(app_configs=None, **kwargs):
    """System check (python manage.py check, arranque): em produção (DEBUG=False) com o vinti4 ligado, os
    endereços da SISP têm de ser os de produção — por omissão são os de teste e os pagamentos iam lá parar."""
    from django.core.checks import Warning as Aviso      # aviso, não erro: um erro parava o worker e os comandos
    import sys
    if not em_uso() or settings.DEBUG or 'test' in sys.argv[1:2]:       # os testes correm com DEBUG=False
        return []
    problemas = []
    if ambiente() == 'teste':
        problemas.append(Aviso('vinti4 ligado em produção com os endereços de TESTE da SISP',
                               hint='Define VINTI4_URL e VINTI4_ESTADO_URL com os endereços de produção que a SISP enviar.',
                               id='bendi.vinti4.W000'))
    if not settings.VINTI4_MERCHANT_ID.strip():
        problemas.append(Aviso('VINTI4_MERCHANT_ID por definir: os ficheiros VBVT da Bendi são recusados',
                               id='bendi.vinti4.W001'))
    if not (settings.VINTI4_PORTAL_ID.strip() and settings.VINTI4_PORTAL_PASSWORD.strip()):
        problemas.append(Aviso('VINTI4_PORTAL_ID/VINTI4_PORTAL_PASSWORD por definir: os pagamentos sem resposta '
                               'ficam por confirmar (sem API de estado)', id='bendi.vinti4.W002'))
    return problemas


# ── credenciais ─────────────────────────────────────────────────

@dataclass
class Credenciais:
    pos_id: str
    chave: str = field(repr=False)      # nunca aparece em logs nem no Sentry


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
    """'+238 991 12 23' → {'cc': '238', 'subscriber': '9911223'} | None.
    Escrito com indicativo ('+351 …' ou '00351 …'), vale o indicativo escrito, mesmo que o país da conta seja outro
    (o OTP do 3-D Secure vai para este número); sem ele, usa o do país da conta."""
    from ..utils import geografia
    texto = str(telefone or '').strip()
    digitos = re.sub(r'\D', '', texto)
    internacional = texto.startswith('+') or digitos.startswith('00')
    if digitos.startswith('00'):
        digitos = digitos[2:]
    if not digitos:
        return None
    if internacional:
        conhecidos = {re.sub(r'\D', '', p[2]) for p in geografia.PAISES}
        escrito = next((digitos[:n] for n in (3, 2, 1) if digitos[:n] in conhecidos and len(digitos) > n + 5), None)
        if escrito:
            return {'cc': escrito, 'subscriber': digitos[len(escrito):][:15]}
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
    limpos = {str(k)[:60]: ('…' if k in CAMPOS_SESSAO and v else
                            v if isinstance(v, (bool, int, float)) or v is None else str(v)[:400])
              for k, v in list((campos or {}).items())[:60]}
    tx.respostas = (list(tx.respostas or []) + [{'em': timezone.now().isoformat(timespec='seconds'),
                                                  'origem': origem, 'campos': limpos}])[-MAX_RESPOSTAS:]


def _cancelou(d):
    return _txt(d.get('userCancelled') or d.get('UserCancelled')).lower() == 'true'


def _sessao_certa(tx, d):
    """O cancelamento da SISP não leva FingerPrint, mas traz o merchantSession (aleatório, só foi no formulário
    para a SISP — nunca nos endereços do site): sem ele certo, quem só sabe o merchantRef não cancela nada."""
    return bool(tx.sessao) and _igual(_txt(d.get('merchantSession') or d.get('merchantRespMerchantSession')), tx.sessao)


def _avisar_assinatura_invalida(tx, tipo):
    """Resposta com o resultFingerPrint errado (alguém a forjar uma resposta, ou a chave mal configurada):
    fica no registo e os admins são avisados — um aviso por hora."""
    from datetime import timedelta
    from ..models import Notificacao
    from ..Views.notificacaoView import notificar_admins
    titulo = 'vinti4: resposta com assinatura inválida'
    if Notificacao.objects.filter(tipo='pagamento_erro', titulo__startswith=titulo,
                                  data_criacao__gte=timezone.now() - timedelta(hours=1)).exists():
        return
    notificar_admins(tipo='pagamento_erro', titulo=f'{titulo} — {tx.ref}',
                     mensagem=f'Chegou uma resposta de {tipo} para {tx.ref} ({tx.referencia}) com o resultFingerPrint '
                              f'errado — foi ignorada. Se se repetir, confirma o posAutCode'
                              + (' do contrato da loja.' if tx.loja_id else ' da Bendi (VINTI4_POS_AUT_CODE).'),
                     loja=tx.loja, link='/admin/pagamentos', email=2)


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
                _avisar_assinatura_invalida(tx, 'sucesso')
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
            # o middleware 3DS da SISP assina os erros com a fórmula de SUCESSO (visto em testes reais, 2026-11-12);
            # o Protocolo de Segurança descreve outra — aceitam-se as duas (ambas precisam da chave)
            fp = d.get('resultFingerPrint')
            if not (_igual(fp, fingerprint_erro(chave, d)) or _igual(fp, fingerprint_sucesso(chave, d))):
                log.warning('vinti4: resultFingerPrint inválido na resposta de erro de %s', tx.ref)
                _registar(tx, 'cartao_assinatura_invalida', anterior)
                _avisar_assinatura_invalida(tx, 'erro')
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
            if not _sessao_certa(tx, d):
                log.warning('vinti4: cancelamento sem o merchantSession certo para %s', tx.ref)
                _registar(tx, 'cartao_cancelamento_invalido', anterior)
                return tx
            if tx.estado in ('iniciada', 'por_confirmar'):
                tx.estado, tx.terminada_em = 'cancelada', timezone.now()
                tx.save(update_fields=['estado', 'terminada_em'])
                _registar(tx, 'cartao_cancelado', anterior)
            return tx
        log.warning('vinti4: resposta sem messageType nem cancelamento para %s', tx.ref)
        return tx


# ── API de estado (Plan Test 38–41) ────────────────────────────

class _CertificadoFixo(HTTPAdapter):
    """Aceita o servidor só se o certificado tiver esta impressão digital SHA-256 (urllib3 assert_fingerprint).
    Substitui a verificação pela CA — que falha num certificado auto-assinado — por uma comparação exacta."""

    def __init__(self, impressao):
        self._impressao = impressao
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        kwargs['assert_fingerprint'] = self._impressao
        super().init_poolmanager(*args, **kwargs)

    def send(self, request, **kwargs):
        kwargs['verify'] = False        # a verificação passa a ser a impressão digital acima (não fica desligada)
        return super().send(request, **kwargs)


def _sessao_estado():
    """Sessão para a API de estado. No servidor de TESTE da SISP (*.teste.sisp.cv, certificado auto-assinado) o
    certificado tem de ter a impressão digital VINTI4_ESTADO_CERT_SHA256; em qualquer outro servidor (produção),
    verificação normal pela CA."""
    sessao = requests.Session()
    host = (urlsplit(settings.VINTI4_ESTADO_URL).hostname or '').lower()
    impressao = re.sub(r'[^0-9a-f]', '', (settings.VINTI4_ESTADO_CERT_SHA256 or '').lower())
    if host.endswith('.teste.sisp.cv') and len(impressao) == 64:
        sessao.mount('https://', _CertificadoFixo(impressao))
    return sessao


def consultar_estado(tx):
    """Pergunta à SISP se a transacção foi paga → 'paga' | 'nao_paga' | None (sem API, sem resposta ou recusada)."""
    return consultar(tx)[0]


def consultar(tx):
    """→ (resultado, corpo da resposta da API ou None). Bendi: o Portal das settings; loja: o Portal que ela indicou
    na adesão (utils/vinti4.guardar_portal) — sem ele, a transacção fica por confirmar."""
    if tx.loja_id is None:
        portal, password = settings.VINTI4_PORTAL_ID.strip(), settings.VINTI4_PORTAL_PASSWORD.strip()
    else:
        from ..utils import vinti4 as adesoes
        portal, password = adesoes.portal(tx.loja) or ('', '')
    if not (portal and password and settings.VINTI4_ESTADO_URL):
        return None, None
    try:
        cred = _credenciais_da(tx)
        with _sessao_estado() as sessao:
            resp = sessao.post(settings.VINTI4_ESTADO_URL, auth=(portal, password), timeout=15,
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
    from django.db.models import F, Q
    from ..models import TransacaoVinti4
    agora = agora or timezone.now()
    por_confirmar = Q(estado='por_confirmar', criada_em__gt=agora - PRAZO_CONSULTAS) & (
        Q(consultada_em__isnull=True)
        | Q(consultas__lt=CONSULTAS_MAX, consultada_em__lt=agora - INTERVALO_CONSULTAS)
        | Q(consultas__gte=CONSULTAS_MAX, consultada_em__lt=agora - INTERVALO_LENTO))
    candidatas = (TransacaoVinti4.objects.filter(Q(estado='iniciada', criada_em__lt=agora - TEMPO_LIMITE) | por_confirmar)
                  .order_by(F('consultada_em').asc(nulls_first=True), 'id').values_list('id', flat=True)[:50])
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
                tx.consultas += 1           # sem Portal configurado (corpo None) não conta: quando chegar, pergunta-se
            tx.consultada_em = agora
            _mudar_pela_consulta(tx, resultado, agora)
            if tx.estado == anterior and resultado is None:
                tx.estado = 'por_confirmar'
            tx.save()
            if tx.estado != anterior:
                mudaram += 1
                _registar(tx, f'cartao_{tx.estado}', anterior)
                if tx.estado == 'por_confirmar':
                    transaction.on_commit(lambda t=tx: _avisar_por_confirmar(t))
            if tx.estado == 'paga':
                _aplicar(tx)
    return mudaram


def _avisar_por_confirmar(tx):
    """Uma transacção ficou por confirmar (sem resposta da SISP e a API de estado não respondeu): os admins e, se o
    pagamento é de uma loja, o dono — para confirmarem no Portal do Comerciante e fecharem à mão. Uma vez por
    transacção (só na passagem de iniciada a por confirmar); o worker continua a perguntar à SISP."""
    from ..Views.notificacaoView import notificar_admins, notificar_staff
    from ..utils.fila_emails import IMPORTANTE
    titulo = f'Pagamento com cartão por confirmar — {tx.ref}'
    msg = (f'Não chegou resposta da SISP ao pagamento {tx.ref} ({tx.montante} CVE, {tx.descricao or tx.referencia}) e '
           f'não foi possível perguntar-lhe o estado. Vê no Portal do Comerciante se o pagamento existe e confirma-o '
           f'em Pagamentos → Cartão ("Foi paga" / "Não foi paga"). Entretanto continuamos a perguntar à SISP.')
    chave = f'por_confirmar:{tx.id}'
    try:
        if tx.loja_id:
            notificar_staff(tx.loja, ['dono'], 'vinti4', titulo, msg, link=f'/loja/{tx.loja_id}/backoffice/pagamentos',
                            email=IMPORTANTE, email_chave=chave)
        notificar_admins('vinti4', titulo, msg, loja=tx.loja, link='/admin/pagamentos', email=IMPORTANTE,
                         email_chave=chave)
    except Exception:          # o estado já está gravado: o aviso não o pode estragar
        log.exception('vinti4: aviso de pagamento por confirmar falhou (%s)', tx.ref)


def _mudar_pela_consulta(tx, resultado, agora):
    """Transacção ainda em aberto + o que a API de estado disse → muda o estado (não grava)."""
    if resultado == 'paga':
        tx.estado, tx.confirmada_por, tx.terminada_em = 'paga', 'estado', agora
    elif resultado == 'nao_paga':
        tx.estado, tx.terminada_em, tx.mensagem = 'expirada', agora, 'Sem resposta da SISP: o pagamento não foi feito.'


def consultar_agora(tx_id):
    """Admin → "Perguntar à SISP" (Plan Test 39–41, e as que ficaram por confirmar ou que o VBVT diz aprovadas).
    Pergunta sempre, mesmo a uma transacção já terminada (fica só registado o que a SISP disse); muda o estado só
    se estiver em aberto: paga → aplica o pagamento; não paga → sem resposta, mas só passados os 8 minutos (antes
    disso o cliente pode ainda estar na página da SISP). → (tx, resultado, corpo)."""
    from ..models import TransacaoVinti4
    tx = TransacaoVinti4.objects.select_related('loja').get(pk=tx_id)
    resultado, corpo = consultar(tx)
    if corpo is None:
        raise ErroPagamento('A API de estado não está configurada: falta o Portal ID e a password do Portal do '
                            'Comerciante' + (' desta loja.' if tx.loja_id else ' (VINTI4_PORTAL_ID / VINTI4_PORTAL_PASSWORD).'))
    agora = timezone.now()
    with transaction.atomic():
        tx = TransacaoVinti4.objects.select_for_update(of=('self',)).select_related('loja').get(pk=tx_id)
        anterior = tx.estado
        _guardar_resposta(tx, 'estado', {**corpo, 'pedido_por': 'admin'})
        if tx.estado in ('iniciada', 'por_confirmar'):
            if resultado == 'paga' or (resultado == 'nao_paga' and tx.criada_em <= agora - TEMPO_LIMITE):
                _mudar_pela_consulta(tx, resultado, agora)
        tx.save()
        if tx.estado != anterior:
            _registar(tx, f'cartao_{tx.estado}', anterior)
        if tx.estado == 'paga' and anterior != 'paga':
            _aplicar(tx)
    return tx, resultado, corpo


def resolver_a_mao(tx_id, resultado, nota, quem, por='admin'):
    """Admin (ou a loja, nas dela) fecha à mão uma transacção sem resposta da SISP, depois de ver no Portal do
    Comerciante se o pagamento existe — para quando a API de estado não responde (SISP em baixo, certificado…).
    resultado 'paga' → aplica o pagamento (como se a resposta tivesse chegado); 'nao_paga' → sem resposta.
    Só as que estão por confirmar, ou iniciadas há mais de 8 minutos (antes disso o cliente pode estar a pagar).
    Fica no registo com quem foi e a nota. Uma resposta da SISP que chegue depois segue o caminho de sempre
    (pagamento tardio → reembolso). → tx."""
    from ..models import TransacaoVinti4
    if resultado not in ('paga', 'nao_paga'):
        raise ErroPagamento('Escolhe "paga" ou "não paga".')
    nota = ' '.join(str(nota or '').split())
    if len(nota) < 5:
        raise ErroPagamento('Escreve uma nota (pelo menos 5 caracteres): o que viste no Portal do Comerciante.')
    nota = nota[:300]
    agora = timezone.now()
    with transaction.atomic():
        tx = TransacaoVinti4.objects.select_for_update(of=('self',)).select_related('loja').get(pk=tx_id)
        aberta = tx.estado == 'por_confirmar' or (tx.estado == 'iniciada' and tx.criada_em <= agora - TEMPO_LIMITE)
        if not aberta:
            raise ErroPagamento('Só se confirma à mão um pagamento sem resposta da SISP (por confirmar, ou iniciado '
                                'há mais de 8 minutos).' if tx.estado == 'iniciada' else
                                f'Este pagamento já está terminado ({tx.get_estado_display().lower()}).')
        anterior = tx.estado
        _guardar_resposta(tx, 'manual', {'resultado': resultado, 'nota': nota, 'por': getattr(quem, 'username', '')})
        tx.terminada_em = agora
        if resultado == 'paga':
            tx.estado, tx.confirmada_por = 'paga', por
        else:
            tx.estado = 'expirada'
            tx.mensagem = 'Sem resposta da SISP: o pagamento não foi feito.'
        tx.save()
        _registar(tx, f'cartao_{tx.estado}', anterior)
        if tx.estado == 'paga':
            _aplicar(tx)
    return tx


def _sem_outro_a_decorrer(referencia):
    """Um pagamento com cartão de cada vez para a mesma encomenda/marcação/fatura/cobrança: com outro ainda na
    página da SISP (iniciado há menos de 8 minutos, sem resposta) podiam ficar os dois cobrados. Quem cancela na
    página da SISP fica livre logo; quem só fecha a página espera o fim dos 8 minutos."""
    from ..models import TransacaoVinti4
    from .servico import ler_referencia
    lido = ler_referencia(referencia)
    if not lido:
        return
    agora = timezone.now()
    aberta = (TransacaoVinti4.objects.filter(referencia__startswith=f'{lido[0]}-{lido[1]}-', estado='iniciada',
                                             criada_em__gt=agora - TEMPO_LIMITE).order_by('-criada_em').first())
    if aberta:
        falta = max(1, int((aberta.criada_em + TEMPO_LIMITE - agora).total_seconds() // 60) + 1)
        raise ErroPagamento(f'Já há um pagamento com cartão a decorrer para isto. Se fechaste a página da SISP sem '
                            f'pagar, tenta outra vez dentro de {falta} min — assim não pagas duas vezes.')


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
        _sem_outro_a_decorrer(cobranca.referencia)
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
        raise ErroPagamento(mensagens.get(tx.estado, 'O pagamento não foi concluído.'), destino_ref=tx.referencia,
                            pendente=tx.estado in ('iniciada', 'por_confirmar'))

    def reembolsar(self, transacao, valor, chave=''):
        raise ErroPagamento('Os pagamentos com cartão vinti4 devolvem-se com um estorno no Portal do Comerciante '
                            'da SISP.', estorno_loja=True)


def _moeda():
    from ..utils.dinheiro import moeda_cobranca
    return moeda_cobranca('vinti4')


FORNECEDOR = Vinti4()
