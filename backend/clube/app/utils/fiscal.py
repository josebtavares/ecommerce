"""
Dados fiscais de quem vende (loja ou POS) e faturas registadas nas encomendas.

O Bende ainda não emite faturas pelo e-Fatura: cada vendedor emite as suas (Emissor Público da DNRE
ou o seu programa) e regista o número/PDF na encomenda. Aqui fica:
- NIF + regime ('particular' = vendas ocasionais, 'atividade' = atividade declarada) + a declaração
  de responsabilidade aceite no registo;
- a validação do registo de uma fatura numa encomenda.
"""
import re

from django.utils import timezone

REGIMES = [
    ('particular', 'Particular — vendas ocasionais'),
    ('atividade',  'Com atividade declarada'),
]
REGIMES_VALIDOS = {r for r, _ in REGIMES}

FATURA_PDF_MAX_MB = 5
# a fatura só se regista numa venda que aconteceu (não pendente de pagamento, nem cancelada)
ESTADOS_FATURAVEIS = ('pago', 'preparando', 'enviado', 'concluido')


def _verdadeiro(v):
    # FormData manda strings ('true', 'on', '1')
    return v is True or str(v).strip().lower() in ('true', '1', 'on', 'sim')


def validar_dados_fiscais(data):
    """data: request.data com nif, regime_fiscal, declaracao_fiscal. Devolve (dados, erros)."""
    erros = {}
    nif = re.sub(r'\D', '', str(data.get('nif') or ''))
    if len(nif) != 9:
        erros['nif'] = 'O NIF tem 9 dígitos.'
    regime = str(data.get('regime_fiscal') or '').strip()
    if regime not in REGIMES_VALIDOS:
        erros['regime_fiscal'] = 'Escolhe se vendes como particular ou com atividade declarada.'
    if not _verdadeiro(data.get('declaracao_fiscal')):
        erros['declaracao_fiscal'] = 'Tens de aceitar a declaração de responsabilidade fiscal.'
    if erros:
        return None, erros
    return {'nif': nif, 'regime_fiscal': regime}, {}


def aplicar_dados_fiscais(obj, dados):
    """Grava NIF/regime na Loja ou ConfiguracaoPOS; a data da declaração é a deste momento."""
    obj.nif = dados['nif']
    obj.regime_fiscal = dados['regime_fiscal']
    obj.dados_fiscais_aceites_em = timezone.now()
    obj.save(update_fields=['nif', 'regime_fiscal', 'dados_fiscais_aceites_em'])


def dados_fiscais_payload(obj):
    """Só para o dono/backoffice — o NIF nunca vai nos dados públicos da loja."""
    return {
        'nif': obj.nif,
        'regime_fiscal': obj.regime_fiscal,
        'completos': bool(obj.nif and obj.regime_fiscal and obj.dados_fiscais_aceites_em),
        'aceites_em': obj.dados_fiscais_aceites_em,
    }


def validar_fatura(numero, pdf):
    """Devolve (numero_limpo, erro)."""
    numero = (numero or '').strip()
    if not numero:
        return None, 'Indica o número da fatura.'
    if len(numero) > 60:
        return None, 'O número da fatura tem no máximo 60 caracteres.'
    if pdf:
        if not pdf.name.lower().endswith('.pdf') or (pdf.content_type or '') not in ('application/pdf', 'application/octet-stream'):
            return None, 'A fatura tem de ser um PDF.'
        if pdf.size > FATURA_PDF_MAX_MB * 1024 * 1024:
            return None, f'O PDF tem no máximo {FATURA_PDF_MAX_MB} MB.'
        if pdf.read(5) != b'%PDF-':
            return None, 'O ficheiro não é um PDF válido.'
        pdf.seek(0)
    return numero, None
